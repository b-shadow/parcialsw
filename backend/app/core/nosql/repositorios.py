from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.nosql.contratos import (
    ColeccionMongo,
    DocumentoAuditoriaOperativa,
    DocumentoDiagramaUML,
    DocumentoInstantaneaContextoIA,
    DocumentoMensajeIA,
    DocumentoMongo,
    DocumentoPuntoControlMigracion,
    DocumentoVersionDiagramaUML,
)
from app.core.nosql.nombres_mongo import adaptar_mongo


class RepositorioMongo[DocumentT: DocumentoMongo]:
    def __init__(self, database: Any, collection: ColeccionMongo, model: type[DocumentT]) -> None:
        self.collection = adaptar_mongo(database)[collection.value]
        self.model = model

    async def get(self, document_id: UUID) -> DocumentT | None:
        document = await self.collection.find_one({"_id": str(document_id)})
        return self.model.model_validate(document) if document else None

    async def upsert(self, document: DocumentT) -> DocumentT:
        payload = document.to_mongo()
        payload["updated_at"] = datetime.now(UTC)
        result = await self.collection.find_one_and_replace(
            {"_id": payload["_id"]},
            payload,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return self.model.model_validate(result)

    async def delete(self, document_id: UUID) -> bool:
        result = await self.collection.delete_one({"_id": str(document_id)})
        return result.deleted_count == 1

    async def count(self, filters: Mapping[str, Any] | None = None) -> int:
        return await self.collection.count_documents(dict(filters or {}))


class RepositorioDiagramasUML(RepositorioMongo[DocumentoDiagramaUML]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, ColeccionMongo.UML_DIAGRAMS, DocumentoDiagramaUML)

    async def obtener_por_proyecto(self, project_id: UUID) -> DocumentoDiagramaUML | None:
        document = await self.collection.find_one({"project_id": str(project_id)})
        return self.model.model_validate(document) if document else None

    async def reemplazar_si_revision(
        self,
        document: DocumentoDiagramaUML,
        *,
        expected_revision: int,
    ) -> DocumentoDiagramaUML | None:
        if document.revision != expected_revision + 1:
            raise ValueError("new UML revision must increment expected_revision exactly once")
        from app.modules.modelado_uml.engine.modelo_interno import ModeloDiagramaUML
        from app.modules.modelado_uml.engine.validador import validar_modelo_interno

        model = ModeloDiagramaUML.model_validate(document.content)
        if str(model.id) != str(document.id) or str(model.project_id) != str(document.project_id):
            raise ValueError("UML document identity does not match its content")
        errors, _, _ = validar_modelo_interno(model)
        if errors:
            raise ValueError("invalid UML document references: " + "; ".join(errors))
        payload = document.to_mongo()
        result = await self.collection.find_one_and_replace(
            {"_id": payload["_id"], "revision": expected_revision},
            payload,
            return_document=ReturnDocument.AFTER,
        )
        return self.model.model_validate(result) if result else None


class RepositorioVersionesDiagramaUML(RepositorioMongo[DocumentoVersionDiagramaUML]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, ColeccionMongo.UML_DIAGRAM_VERSIONS, DocumentoVersionDiagramaUML)

    async def insertar_inmutable(
        self, document: DocumentoVersionDiagramaUML
    ) -> DocumentoVersionDiagramaUML:
        payload = document.to_mongo()
        try:
            await self.collection.insert_one(payload)
            return document
        except DuplicateKeyError:
            existing = await self.collection.find_one({"_id": payload["_id"]})
            if existing and existing.get("content_hash") == document.content_hash:
                return self.model.model_validate(existing)
            raise ValueError(
                "immutable UML version already exists with different content"
            ) from None


class RepositorioMensajesIA(RepositorioMongo[DocumentoMensajeIA]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, ColeccionMongo.AI_MESSAGES, DocumentoMensajeIA)

    async def listar_por_conversacion(
        self, conversation_id: UUID, *, after_sequence: int = 0, limit: int = 100
    ) -> list[DocumentoMensajeIA]:
        cursor = (
            self.collection.find(
                {
                    "conversation_id": str(conversation_id),
                    "sequence_number": {"$gt": after_sequence},
                }
            )
            .sort("sequence_number", 1)
            .limit(max(1, min(limit, 500)))
        )
        return [self.model.model_validate(document) async for document in cursor]


class RepositorioInstantaneasContextoIA(RepositorioMongo[DocumentoInstantaneaContextoIA]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, ColeccionMongo.AI_CONTEXT_SNAPSHOTS, DocumentoInstantaneaContextoIA)


class RepositorioPuntosControlMigracion(RepositorioMongo[DocumentoPuntoControlMigracion]):
    def __init__(self, database: Any) -> None:
        super().__init__(
            database, ColeccionMongo.MIGRATION_CHECKPOINTS, DocumentoPuntoControlMigracion
        )

    async def obtener_por_nombre(self, name: str) -> DocumentoPuntoControlMigracion | None:
        document = await self.collection.find_one({"migration_name": name})
        return self.model.model_validate(document) if document else None


class RepositorioAuditoriasOperativas(RepositorioMongo[DocumentoAuditoriaOperativa]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, ColeccionMongo.OPERATIONAL_AUDITS, DocumentoAuditoriaOperativa)


DOCUMENT_MODELS: dict[ColeccionMongo, type[BaseModel]] = {
    ColeccionMongo.UML_DIAGRAMS: DocumentoDiagramaUML,
    ColeccionMongo.UML_DIAGRAM_VERSIONS: DocumentoVersionDiagramaUML,
    ColeccionMongo.AI_MESSAGES: DocumentoMensajeIA,
    ColeccionMongo.AI_CONTEXT_SNAPSHOTS: DocumentoInstantaneaContextoIA,
    ColeccionMongo.MIGRATION_CHECKPOINTS: DocumentoPuntoControlMigracion,
    ColeccionMongo.OPERATIONAL_AUDITS: DocumentoAuditoriaOperativa,
}
