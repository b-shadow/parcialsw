from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.nosql.contracts import (
    AiContextSnapshotDocument,
    AiMessageDocument,
    MigrationCheckpointDocument,
    MongoCollection,
    MongoDocument,
    OperationalAuditDocument,
    UmlDiagramDocument,
    UmlDiagramVersionDocument,
)


class MongoRepository[DocumentT: MongoDocument]:
    def __init__(self, database: Any, collection: MongoCollection, model: type[DocumentT]) -> None:
        self.collection = database[collection.value]
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


class UmlDiagramRepository(MongoRepository[UmlDiagramDocument]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, MongoCollection.UML_DIAGRAMS, UmlDiagramDocument)

    async def get_by_project(self, project_id: UUID) -> UmlDiagramDocument | None:
        document = await self.collection.find_one({"project_id": str(project_id)})
        return self.model.model_validate(document) if document else None

    async def replace_if_revision(
        self,
        document: UmlDiagramDocument,
        *,
        expected_revision: int,
    ) -> UmlDiagramDocument | None:
        if document.revision != expected_revision + 1:
            raise ValueError("new UML revision must increment expected_revision exactly once")
        from app.modules.modelado_uml.engine.internal_model import UmlDiagramModel
        from app.modules.modelado_uml.engine.validator import validate_internal_model

        model = UmlDiagramModel.model_validate(document.content)
        if str(model.id) != str(document.id) or str(model.project_id) != str(document.project_id):
            raise ValueError("UML document identity does not match its content")
        errors, _, _ = validate_internal_model(model)
        if errors:
            raise ValueError("invalid UML document references: " + "; ".join(errors))
        payload = document.to_mongo()
        result = await self.collection.find_one_and_replace(
            {"_id": payload["_id"], "revision": expected_revision},
            payload,
            return_document=ReturnDocument.AFTER,
        )
        return self.model.model_validate(result) if result else None


class UmlDiagramVersionRepository(MongoRepository[UmlDiagramVersionDocument]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, MongoCollection.UML_DIAGRAM_VERSIONS, UmlDiagramVersionDocument)

    async def insert_immutable(
        self, document: UmlDiagramVersionDocument
    ) -> UmlDiagramVersionDocument:
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


class AiMessageRepository(MongoRepository[AiMessageDocument]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, MongoCollection.AI_MESSAGES, AiMessageDocument)

    async def list_for_conversation(
        self, conversation_id: UUID, *, after_sequence: int = 0, limit: int = 100
    ) -> list[AiMessageDocument]:
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


class AiContextSnapshotRepository(MongoRepository[AiContextSnapshotDocument]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, MongoCollection.AI_CONTEXT_SNAPSHOTS, AiContextSnapshotDocument)


class MigrationCheckpointRepository(MongoRepository[MigrationCheckpointDocument]):
    def __init__(self, database: Any) -> None:
        super().__init__(
            database, MongoCollection.MIGRATION_CHECKPOINTS, MigrationCheckpointDocument
        )

    async def get_by_name(self, name: str) -> MigrationCheckpointDocument | None:
        document = await self.collection.find_one({"migration_name": name})
        return self.model.model_validate(document) if document else None


class OperationalAuditRepository(MongoRepository[OperationalAuditDocument]):
    def __init__(self, database: Any) -> None:
        super().__init__(database, MongoCollection.OPERATIONAL_AUDITS, OperationalAuditDocument)


DOCUMENT_MODELS: dict[MongoCollection, type[BaseModel]] = {
    MongoCollection.UML_DIAGRAMS: UmlDiagramDocument,
    MongoCollection.UML_DIAGRAM_VERSIONS: UmlDiagramVersionDocument,
    MongoCollection.AI_MESSAGES: AiMessageDocument,
    MongoCollection.AI_CONTEXT_SNAPSHOTS: AiContextSnapshotDocument,
    MongoCollection.MIGRATION_CHECKPOINTS: MigrationCheckpointDocument,
    MongoCollection.OPERATIONAL_AUDITS: OperationalAuditDocument,
}
