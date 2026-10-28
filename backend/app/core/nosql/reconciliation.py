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

from app.core.config.settings import settings
from app.core.nosql.contracts import MongoCollection, OperationalAuditDocument
from app.core.nosql.outbox_model import NoSqlOutboxEvent
from app.modules.asistente_proyecto.models import AiConversation, AiMessage
from app.modules.modelado_uml.engine.internal_model import UmlDiagramModel
from app.modules.modelado_uml.engine.validator import validate_internal_model
from app.modules.modelado_uml.models import UmlDiagram
from app.modules.proyectos_colaboracion.models import Project, ProjectVersion


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CollectionAudit:
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
class IntegrityFinding:
    severity: str
    code: str
    collection: str
    document_id: str | None
    detail: str


class ReconciliationService:
    """Read-only drift detector; it never repairs or removes user data."""

    def __init__(self, db: Session, mongo_database: Any) -> None:
        self.db = db
        self.mongo_database = mongo_database

    async def audit_collection(
        self,
        collection: MongoCollection,
        sql_ids: set[str],
        *,
        expected_hashes: dict[str, str] | None = None,
        require_complete: bool = False,
    ) -> CollectionAudit:
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
        return CollectionAudit(
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
            MongoCollection.UML_DIAGRAMS: {
                str(value) for value in self.db.scalars(select(UmlDiagram.id))
            },
            MongoCollection.UML_DIAGRAM_VERSIONS: {
                str(value) for value in self.db.scalars(select(ProjectVersion.id))
            },
        }
        if not settings.nosql_consolidated_mode:
            sources[MongoCollection.AI_MESSAGES] = {
                str(value) for value in self.db.scalars(select(AiMessage.id))
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
                select(Project.id, Project.revision)
            ).tuples()
        }
        diagrams = {
            str(diagram_id): str(project_id)
            for diagram_id, project_id in self.db.execute(
                select(UmlDiagram.id, UmlDiagram.project_id)
            ).tuples()
        }
        conversations = {
            str(conversation_id): str(project_id)
            for conversation_id, project_id in self.db.execute(
                select(AiConversation.id, AiConversation.project_id)
            ).tuples()
        }
        versions = {
            str(version_id): str(project_id)
            for version_id, project_id in self.db.execute(
                select(ProjectVersion.id, ProjectVersion.project_id)
            ).tuples()
        }
        findings: list[IntegrityFinding] = []
        reports: list[dict[str, Any]] = []
        max_size = 0
        max_revision_lag = 0

        async def documents(collection: MongoCollection) -> list[dict[str, Any]]:
            return [item async for item in self.mongo_database[collection.value].find({})]

        uml_documents = await documents(MongoCollection.UML_DIAGRAMS)
        uml_ids = {str(item.get("_id")) for item in uml_documents}
        self._append_identity_findings(
            findings, MongoCollection.UML_DIAGRAMS, set(diagrams), uml_ids
        )
        for document in uml_documents:
            document_id = str(document.get("_id"))
            size = len(BSON.encode(document))
            max_size = max(max_size, size)
            if size > settings.nosql_alert_max_document_bytes:
                findings.append(
                    IntegrityFinding(
                        "error",
                        "DOCUMENT_TOO_LARGE",
                        MongoCollection.UML_DIAGRAMS.value,
                        document_id,
                        f"{size} bytes",
                    )
                )
            expected_project = diagrams.get(document_id)
            if expected_project and str(document.get("project_id")) != expected_project:
                findings.append(
                    IntegrityFinding(
                        "error",
                        "PROJECT_REFERENCE_MISMATCH",
                        MongoCollection.UML_DIAGRAMS.value,
                        document_id,
                        "project_id differs from SQL registry",
                    )
                )
            try:
                model = UmlDiagramModel.model_validate(document.get("content"))
                errors, _, _ = validate_internal_model(model)
                if errors:
                    raise ValueError("; ".join(errors))
                if canonical_sha256(document["content"]) != document.get("content_hash"):
                    findings.append(
                        IntegrityFinding(
                            "error",
                            "CONTENT_HASH_MISMATCH",
                            MongoCollection.UML_DIAGRAMS.value,
                            document_id,
                            "stored hash differs from canonical content",
                        )
                    )
            except (KeyError, TypeError, ValueError) as exc:
                findings.append(
                    IntegrityFinding(
                        "error",
                        "INVALID_UML_DOCUMENT",
                        MongoCollection.UML_DIAGRAMS.value,
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
                        IntegrityFinding(
                            "error",
                            "REVISION_LAG",
                            MongoCollection.UML_DIAGRAMS.value,
                            document_id,
                            f"MongoDB is {lag} revisions behind PostgreSQL",
                        )
                    )

        version_documents = await documents(MongoCollection.UML_DIAGRAM_VERSIONS)
        version_ids = {str(item.get("_id")) for item in version_documents}
        self._append_identity_findings(
            findings, MongoCollection.UML_DIAGRAM_VERSIONS, set(versions), version_ids
        )
        for document in version_documents:
            if str(document.get("project_id")) not in projects:
                findings.append(
                    self._orphan_finding(
                        MongoCollection.UML_DIAGRAM_VERSIONS, document, "project_id"
                    )
                )
            if str(document.get("diagram_id")) not in diagrams:
                findings.append(
                    self._orphan_finding(
                        MongoCollection.UML_DIAGRAM_VERSIONS, document, "diagram_id"
                    )
                )

        message_documents = await documents(MongoCollection.AI_MESSAGES)
        sql_message_ids = (
            {str(value) for value in self.db.scalars(select(AiMessage.id))}
            if not settings.nosql_consolidated_mode
            else set()
        )
        message_ids = {str(item.get("_id")) for item in message_documents}
        if not settings.nosql_consolidated_mode:
            self._append_identity_findings(
                findings, MongoCollection.AI_MESSAGES, sql_message_ids, message_ids
            )
        sequences: Counter[tuple[str, int]] = Counter()
        for document in message_documents:
            conversation_id = str(document.get("conversation_id"))
            sequences[(conversation_id, int(document.get("sequence_number", -1)))] += 1
            if conversation_id not in conversations:
                findings.append(
                    self._orphan_finding(MongoCollection.AI_MESSAGES, document, "conversation_id")
                )
            if str(document.get("project_id")) not in projects:
                findings.append(
                    self._orphan_finding(MongoCollection.AI_MESSAGES, document, "project_id")
                )
        for (conversation_id, sequence), count in sequences.items():
            if count > 1:
                findings.append(
                    IntegrityFinding(
                        "error",
                        "DUPLICATE_MESSAGE_SEQUENCE",
                        MongoCollection.AI_MESSAGES.value,
                        conversation_id,
                        f"sequence {sequence} appears {count} times",
                    )
                )

        contexts = await documents(MongoCollection.AI_CONTEXT_SNAPSHOTS)
        for document in contexts:
            if str(document.get("conversation_id")) not in conversations:
                findings.append(
                    self._orphan_finding(
                        MongoCollection.AI_CONTEXT_SNAPSHOTS, document, "conversation_id"
                    )
                )

        collection_counts = {
            MongoCollection.UML_DIAGRAMS.value: len(uml_documents),
            MongoCollection.UML_DIAGRAM_VERSIONS.value: len(version_documents),
            MongoCollection.AI_MESSAGES.value: len(message_documents),
            MongoCollection.AI_CONTEXT_SNAPSHOTS.value: len(contexts),
        }
        for collection, count in collection_counts.items():
            mongo_collection = self.mongo_database[collection]
            indexes = await mongo_collection.index_information()
            index_usage = {}
            try:
                index_usage = {
                    item["name"]: int(item.get("accesses", {}).get("ops", 0))
                    async for item in mongo_collection.aggregate([{"$indexStats": {}}])
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
            status for status in self.db.scalars(select(NoSqlOutboxEvent.status))
        )
        if outbox_counts["pending"] + outbox_counts["retry"] > settings.nosql_alert_pending_outbox:
            findings.append(
                IntegrityFinding(
                    "error",
                    "OUTBOX_BACKLOG",
                    "nosql_outbox_events",
                    None,
                    "pending and retry events exceed the configured threshold",
                )
            )
        if outbox_counts["dead"] > 0 and outbox_counts["dead"] >= settings.nosql_alert_dead_outbox:
            findings.append(
                IntegrityFinding(
                    "error",
                    "OUTBOX_DEAD_EVENTS",
                    "nosql_outbox_events",
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
                IntegrityFinding(
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
            audit = OperationalAuditDocument(
                _id=uuid4(),
                status=status,
                duration_ms=duration_ms,
                findings=result["findings"],
                metrics=result["metrics"],
                collection_reports=reports,
            )
            await self.mongo_database[MongoCollection.OPERATIONAL_AUDITS.value].insert_one(
                audit.to_mongo()
            )
        return result

    @staticmethod
    def _append_identity_findings(
        findings: list[IntegrityFinding],
        collection: MongoCollection,
        sql_ids: set[str],
        mongo_ids: set[str],
    ) -> None:
        for document_id in sorted(mongo_ids - sql_ids):
            findings.append(
                IntegrityFinding(
                    "error",
                    "ORPHAN_DOCUMENT",
                    collection.value,
                    document_id,
                    "document has no SQL registry row",
                )
            )
        for document_id in sorted(sql_ids - mongo_ids):
            findings.append(
                IntegrityFinding(
                    "error",
                    "MISSING_DOCUMENT",
                    collection.value,
                    document_id,
                    "SQL registry row has no MongoDB document",
                )
            )

    @staticmethod
    def _orphan_finding(
        collection: MongoCollection, document: dict[str, Any], field: str
    ) -> IntegrityFinding:
        return IntegrityFinding(
            "error",
            "ORPHAN_REFERENCE",
            collection.value,
            str(document.get("_id")),
            f"{field} does not exist in PostgreSQL registry",
        )
