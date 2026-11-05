from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from bson import BSON
from pymongo.errors import PyMongoError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.core.nosql.contratos import ColeccionMongo, DocumentoAuditoriaOperativa
from app.core.nosql.modelo_bandeja_salida import EventoBandejaSalidaNoSQL
from app.core.nosql.nombres_mongo import adaptar_mongo
from app.modules.asistente_proyecto.models import ConversacionIA, MensajeIA
from app.modules.modelado_uml.engine.modelo_interno import ModeloDiagramaUML
from app.modules.modelado_uml.engine.validador import validar_modelo_interno
from app.modules.modelado_uml.models import DiagramaUML
from app.modules.proyectos_colaboracion.models import Proyecto, VersionProyecto


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuditoriaColeccion:
    collection: str
    sql_count: int
    mongo_count: int
    orphan_ids: tuple[str, ...]
    missing_ids: tuple[str, ...]
    hash_mismatches: tuple[str, ...]

    @property
    def consistent(self) -> bool:
        return not self.orphan_ids and not self.missing_ids and not self.hash_mismatches


@dataclass(frozen=True)
class HallazgoIntegridad:
    severity: str
    code: str
    collection: str
    document_id: str | None
    detail: str


class ServicioConciliacion:
    """Read-only drift detector; it never repairs or removes user data."""

    def __init__(self, db: Session, mongo_database: Any) -> None:
        self.db = db
        self.mongo_database = adaptar_mongo(mongo_database)

    async def audit_collection(
        self,
        collection: ColeccionMongo,
        sql_ids: set[str],
        *,
        expected_hashes: dict[str, str] | None = None,
        require_complete: bool = False,
    ) -> AuditoriaColeccion:
        documents = [
            document
            async for document in self.mongo_database[collection.value].find(
                {}, {"_id": 1, "content_hash": 1}
            )
        ]
        mongo_ids = {str(document["_id"]) for document in documents}
        hashes = expected_hashes or {}
        mismatches = tuple(
            sorted(
                document_id
                for document_id, expected in hashes.items()
                if document_id in mongo_ids
                and next(
                    (
                        item.get("content_hash")
                        for item in documents
                        if str(item["_id"]) == document_id
                    ),
                    None,
                )
                != expected
            )
        )
        return AuditoriaColeccion(
            collection=collection.value,
            sql_count=len(sql_ids),
            mongo_count=len(mongo_ids),
            orphan_ids=tuple(sorted(mongo_ids - sql_ids)),
            missing_ids=tuple(sorted(sql_ids - mongo_ids)) if require_complete else (),
            hash_mismatches=mismatches,
        )

    async def audit_all(
        self,
        *,
        require_complete: bool = False,
        expected_hashes: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        sources = {
            ColeccionMongo.UML_DIAGRAMS: {
                str(value) for value in self.db.scalars(select(DiagramaUML.id))
            },
            ColeccionMongo.UML_DIAGRAM_VERSIONS: {
                str(value) for value in self.db.scalars(select(VersionProyecto.id))
            },
        }
        if not settings.nosql_consolidated_mode:
            sources[ColeccionMongo.AI_MESSAGES] = {
                str(value) for value in self.db.scalars(select(MensajeIA.id))
            }
        audits = [
            await self.audit_collection(
                collection,
                identifiers,
                expected_hashes=(expected_hashes or {}).get(collection.value),
                require_complete=require_complete,
            )
            for collection, identifiers in sources.items()
        ]
        return {
            "status": "consistent" if all(item.consistent for item in audits) else "drift",
            "require_complete": require_complete,
            "collections": [asdict(item) | {"consistent": item.consistent} for item in audits],
        }

    async def audit_operational(self, *, persist: bool = True) -> dict[str, Any]:
        started = perf_counter()
        projects = {
            str(project_id): revision
            for project_id, revision in self.db.execute(
                select(Proyecto.id, Proyecto.revision)
            ).tuples()
        }
        diagrams = {
            str(diagram_id): str(project_id)
            for diagram_id, project_id in self.db.execute(
                select(DiagramaUML.id, DiagramaUML.project_id)
            ).tuples()
        }
        conversations = {
            str(conversation_id): last_sequence
            for conversation_id, last_sequence in self.db.execute(
                select(ConversacionIA.id, ConversacionIA.last_message_sequence)
            ).tuples()
        }
        versions = {
            str(version_id): str(project_id)
            for version_id, project_id in self.db.execute(
                select(VersionProyecto.id, VersionProyecto.project_id)
            ).tuples()
        }
        findings: list[HallazgoIntegridad] = []
        reports: list[dict[str, Any]] = []
        max_size = 0
        max_revision_lag = 0

        async def documents(collection: ColeccionMongo) -> list[dict[str, Any]]:
            return [item async for item in self.mongo_database[collection.value].find({})]

        uml_documents = await documents(ColeccionMongo.UML_DIAGRAMS)
        uml_ids = {str(item.get("_id")) for item in uml_documents}
        self._agregar_hallazgos_identidad(
            findings, ColeccionMongo.UML_DIAGRAMS, set(diagrams), uml_ids
        )
        for document in uml_documents:
            document_id = str(document.get("_id"))
            size = len(BSON.encode(document))
            max_size = max(max_size, size)
            if size > settings.nosql_alert_max_document_bytes:
                findings.append(
                    HallazgoIntegridad(
                        "error",
                        "DOCUMENT_TOO_LARGE",
                        ColeccionMongo.UML_DIAGRAMS.value,
                        document_id,
                        f"{size} bytes",
                    )
                )
            expected_project = diagrams.get(document_id)
            if expected_project and str(document.get("project_id")) != expected_project:
                findings.append(
                    HallazgoIntegridad(
                        "error",
                        "PROJECT_REFERENCE_MISMATCH",
                        ColeccionMongo.UML_DIAGRAMS.value,
                        document_id,
                        "project_id differs from SQL registry",
                    )
                )
            try:
                model = ModeloDiagramaUML.model_validate(document.get("content"))
                errors = validar_modelo_interno(model)[0] if model.classes else []
                if errors:
                    raise ValueError("; ".join(errors))
                if canonical_sha256(document["content"]) != document.get("content_hash"):
                    findings.append(
                        HallazgoIntegridad(
                            "error",
                            "CONTENT_HASH_MISMATCH",
                            ColeccionMongo.UML_DIAGRAMS.value,
                            document_id,
                            "stored hash differs from canonical content",
                        )
                    )
            except (KeyError, TypeError, ValueError) as exc:
                findings.append(
                    HallazgoIntegridad(
                        "error",
                        "INVALID_UML_DOCUMENT",
                        ColeccionMongo.UML_DIAGRAMS.value,
                        document_id,
                        str(exc)[:500],
                    )
                )
            project_revision = projects.get(str(document.get("project_id")))
            if project_revision is not None:
                lag = project_revision - int(document.get("revision", -1))
                max_revision_lag = max(max_revision_lag, lag)
                if lag > settings.nosql_alert_max_revision_lag:
                    findings.append(
                        HallazgoIntegridad(
                            "error",
                            "REVISION_LAG",
                            ColeccionMongo.UML_DIAGRAMS.value,
                            document_id,
                            f"MongoDB is {lag} revisions behind PostgreSQL",
                        )
                    )

        version_documents = await documents(ColeccionMongo.UML_DIAGRAM_VERSIONS)
        version_ids = {str(item.get("_id")) for item in version_documents}
        self._agregar_hallazgos_identidad(
            findings, ColeccionMongo.UML_DIAGRAM_VERSIONS, set(versions), version_ids
        )
        for document in version_documents:
            if str(document.get("project_id")) not in projects:
                findings.append(
                    self._hallazgo_huerfano(
                        ColeccionMongo.UML_DIAGRAM_VERSIONS, document, "project_id"
                    )
                )
            if str(document.get("diagram_id")) not in diagrams:
                findings.append(
                    self._hallazgo_huerfano(
                        ColeccionMongo.UML_DIAGRAM_VERSIONS, document, "diagram_id"
                    )
                )

        message_documents = await documents(ColeccionMongo.AI_MESSAGES)
        sql_message_ids = (
            {str(value) for value in self.db.scalars(select(MensajeIA.id))}
            if not settings.nosql_consolidated_mode
            else set()
        )
        message_ids = {str(item.get("_id")) for item in message_documents}
        if not settings.nosql_consolidated_mode:
            self._agregar_hallazgos_identidad(
                findings, ColeccionMongo.AI_MESSAGES, sql_message_ids, message_ids
            )
        sequences: Counter[tuple[str, int]] = Counter()
        for document in message_documents:
            conversation_id = str(document.get("conversation_id"))
            sequences[(conversation_id, int(document.get("sequence_number", -1)))] += 1
            if conversation_id not in conversations:
                findings.append(
                    self._hallazgo_huerfano(ColeccionMongo.AI_MESSAGES, document, "conversation_id")
                )
            if str(document.get("project_id")) not in projects:
                findings.append(
                    self._hallazgo_huerfano(ColeccionMongo.AI_MESSAGES, document, "project_id")
                )
        for (conversation_id, sequence), count in sequences.items():
            if count > 1:
                findings.append(
                    HallazgoIntegridad(
                        "error",
                        "DUPLICATE_MESSAGE_SEQUENCE",
                        ColeccionMongo.AI_MESSAGES.value,
                        conversation_id,
                        f"sequence {sequence} appears {count} times",
                    )
                )
        message_sequences: dict[str, set[int]] = {}
        for conversation_id, sequence in sequences:
            message_sequences.setdefault(conversation_id, set()).add(sequence)
        for conversation_id, last_sequence in conversations.items():
            actual = message_sequences.get(conversation_id, set())
            valid_count = sum(1 for sequence in actual if 1 <= sequence <= last_sequence)
            missing = last_sequence - valid_count
            unexpected = len(actual) - valid_count
            if missing or unexpected:
                findings.append(
                    HallazgoIntegridad(
                        "error",
                        "MISSING_CONVERSATION_MESSAGES",
                        ColeccionMongo.AI_MESSAGES.value,
                        conversation_id,
                        f"{missing} missing and {unexpected} unexpected sequences "
                        f"for {last_sequence} recorded messages",
                    )
                )

        contexts = await documents(ColeccionMongo.AI_CONTEXT_SNAPSHOTS)
        for document in contexts:
            if str(document.get("conversation_id")) not in conversations:
                findings.append(
                    self._hallazgo_huerfano(
                        ColeccionMongo.AI_CONTEXT_SNAPSHOTS, document, "conversation_id"
                    )
                )

        collection_counts = {
            ColeccionMongo.UML_DIAGRAMS.value: len(uml_documents),
            ColeccionMongo.UML_DIAGRAM_VERSIONS.value: len(version_documents),
            ColeccionMongo.AI_MESSAGES.value: len(message_documents),
            ColeccionMongo.AI_CONTEXT_SNAPSHOTS.value: len(contexts),
        }
        for collection, count in collection_counts.items():
            mongo_collection = self.mongo_database[collection]
            indexes = await mongo_collection.index_information()
            index_usage = {}
            try:
                index_cursor = await mongo_collection.aggregate([{"$indexStats": {}}])
                index_usage = {
                    item["name"]: int(item.get("accesses", {}).get("ops", 0))
                    async for item in index_cursor
                }
            except (AttributeError, KeyError, TypeError, PyMongoError):
                index_usage = {}
            try:
                stats = await self.mongo_database.command("collStats", collection)
            except (TypeError, ValueError, PyMongoError):
                stats = {}
            reports.append(
                {
                    "collection": collection,
                    "documents": count,
                    "indexes": sorted(indexes),
                    "index_operations": index_usage,
                    "storage_bytes": int(stats.get("storageSize", 0)),
                    "average_document_bytes": int(stats.get("avgObjSize", 0)),
                }
            )

        outbox_counts = Counter(
            status for status in self.db.scalars(select(EventoBandejaSalidaNoSQL.status))
        )
        if outbox_counts["pending"] + outbox_counts["retry"] > settings.nosql_alert_pending_outbox:
            findings.append(
                HallazgoIntegridad(
                    "error",
                    "OUTBOX_BACKLOG",
                    "bandeja_salida_nosql",
                    None,
                    "pending and retry events exceed the configured threshold",
                )
            )
        if outbox_counts["dead"] > 0 and outbox_counts["dead"] >= settings.nosql_alert_dead_outbox:
            findings.append(
                HallazgoIntegridad(
                    "error",
                    "OUTBOX_DEAD_EVENTS",
                    "bandeja_salida_nosql",
                    None,
                    f"{outbox_counts['dead']} dead events",
                )
            )

        ping_started = perf_counter()
        await self.mongo_database.command("ping")
        mongo_latency_ms = round((perf_counter() - ping_started) * 1000, 2)
        hello = await self.mongo_database.command("hello")
        writable = bool(hello.get("isWritablePrimary", hello.get("ismaster", True)))
        if not writable:
            findings.append(
                HallazgoIntegridad(
                    "error",
                    "MONGODB_NOT_WRITABLE",
                    "mongodb",
                    None,
                    "the selected MongoDB node is not writable",
                )
            )
        duration_ms = max(0, round((perf_counter() - started) * 1000))
        status = "healthy" if not findings else "degraded"
        result = {
            "status": status,
            "checked_at": datetime.now(UTC).isoformat(),
            "duration_ms": duration_ms,
            "findings": [asdict(item) for item in findings],
            "metrics": {
                "mongodb_ping_ms": mongo_latency_ms,
                "max_document_bytes": max_size,
                "max_revision_lag": max_revision_lag,
                "outbox": dict(outbox_counts),
                "mongodb_topology": {
                    "replica_set": hello.get("setName"),
                    "writable": writable,
                    "hosts": len(hello.get("hosts", [])),
                },
            },
            "collections": reports,
        }
        if persist:
            audit = DocumentoAuditoriaOperativa(
                _id=uuid4(),
                status=status,
                duration_ms=duration_ms,
                findings=result["findings"],
                metrics=result["metrics"],
                collection_reports=reports,
            )
            await self.mongo_database[ColeccionMongo.OPERATIONAL_AUDITS.value].insert_one(
                audit.to_mongo()
            )
        return result

    @staticmethod
    def _agregar_hallazgos_identidad(
        findings: list[HallazgoIntegridad],
        collection: ColeccionMongo,
        sql_ids: set[str],
        mongo_ids: set[str],
    ) -> None:
        for document_id in sorted(mongo_ids - sql_ids):
            findings.append(
                HallazgoIntegridad(
                    "error",
                    "ORPHAN_DOCUMENT",
                    collection.value,
                    document_id,
                    "document has no SQL registry row",
                )
            )
        for document_id in sorted(sql_ids - mongo_ids):
            findings.append(
                HallazgoIntegridad(
                    "error",
                    "MISSING_DOCUMENT",
                    collection.value,
                    document_id,
                    "SQL registry row has no MongoDB document",
                )
            )

    @staticmethod
    def _hallazgo_huerfano(
        collection: ColeccionMongo, document: dict[str, Any], field: str
    ) -> HallazgoIntegridad:
        return HallazgoIntegridad(
            "error",
            "ORPHAN_REFERENCE",
            collection.value,
            str(document.get("_id")),
            f"{field} does not exist in PostgreSQL registry",
        )
