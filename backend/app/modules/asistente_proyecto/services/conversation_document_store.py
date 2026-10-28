from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from pymongo.errors import PyMongoError
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.nosql.client import MongoManager, mongo_manager
from app.core.nosql.contracts import (
    AiContextSnapshotDocument,
    AiMessageDocument,
    MongoCollection,
    MongoMutation,
)
from app.core.nosql.errors import MongoUnavailableError
from app.core.nosql.outbox import NoSqlOutboxService
from app.core.nosql.reconciliation import canonical_sha256
from app.core.nosql.sync_client import SyncMongoManager, sync_mongo_manager
from app.modules.asistente_proyecto.models import AiConversation, AiMessage

logger = logging.getLogger(__name__)


def _message_payload(message: AiMessage | AiMessageDocument) -> dict[str, Any]:
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "project_id": str(message.project_id),
        "author_user_id": str(message.author_user_id) if message.author_user_id else None,
        "role": message.role,
        "content": message.content,
        "sequence_number": message.sequence_number,
        "client_message_id": str(message.client_message_id) if message.client_message_id else None,
        "correlation_id": str(message.correlation_id),
        "status": message.status,
        "detected_intents": list(message.detected_intents),
        "references_json": list(message.references_json),
        "metadata_json": dict(message.metadata_json),
    }


def message_content_hash(message: AiMessage | AiMessageDocument) -> str:
    return canonical_sha256(_message_payload(message))


def message_document_from_sql(message: AiMessage) -> AiMessageDocument:
    now = datetime.now(UTC)
    return AiMessageDocument(
        _id=message.id,
        project_id=message.project_id,
        conversation_id=message.conversation_id,
        author_user_id=message.author_user_id,
        role=message.role,
        content=message.content,
        sequence_number=message.sequence_number,
        client_message_id=message.client_message_id,
        correlation_id=message.correlation_id,
        status=message.status,
        detected_intents=list(message.detected_intents),
        references_json=list(message.references_json),
        metadata_json=dict(message.metadata_json),
        content_hash=message_content_hash(message),
        created_at=message.created_at or now,
        updated_at=message.updated_at or now,
    )


def enqueue_message_document(db: Session, message: AiMessage) -> AiMessageDocument:
    db.flush()
    document = message_document_from_sql(message)
    mutation = MongoMutation(
        collection=MongoCollection.AI_MESSAGES,
        operation="upsert",
        document_id=message.id,
        document=document.to_mongo(),
    )
    NoSqlOutboxService(db).enqueue(
        aggregate_type="ai_message",
        aggregate_id=message.id,
        mutation=mutation,
        idempotency_key=f"ai-message:{message.id}:{document.content_hash}",
    )
    return document


def context_snapshot_document(
    conversation: AiConversation,
    *,
    summary: str,
    context: dict[str, Any],
    until_sequence: int,
) -> AiContextSnapshotDocument:
    snapshot_id = uuid5(
        NAMESPACE_URL,
        f"case-inteligente:conversation:{conversation.id}:summary:{until_sequence}",
    )
    content_hash = canonical_sha256(
        {
            "conversation_id": str(conversation.id),
            "until_sequence": until_sequence,
            "summary": summary,
            "context": context,
        }
    )
    return AiContextSnapshotDocument(
        _id=snapshot_id,
        project_id=conversation.project_id,
        conversation_id=conversation.id,
        until_sequence=until_sequence,
        summary=summary,
        context=context,
        content_hash=content_hash,
    )


def enqueue_context_snapshot(
    db: Session,
    conversation: AiConversation,
    *,
    summary: str,
    context: dict[str, Any],
    until_sequence: int,
) -> AiContextSnapshotDocument:
    document = context_snapshot_document(
        conversation,
        summary=summary,
        context=context,
        until_sequence=until_sequence,
    )
    NoSqlOutboxService(db).enqueue(
        aggregate_type="ai_context_snapshot",
        aggregate_id=document.id,
        mutation=MongoMutation(
            collection=MongoCollection.AI_CONTEXT_SNAPSHOTS,
            operation="upsert",
            document_id=document.id,
            document=document.to_mongo(),
        ),
        idempotency_key=f"ai-context:{conversation.id}:{until_sequence}:{document.content_hash}",
    )
    return document


class ConversationDocumentStore:
    def __init__(self, manager: MongoManager = mongo_manager, *, database=None) -> None:
        self.manager = manager
        self._database = database

    @property
    def database(self):
        return self._database if self._database is not None else self.manager.database

    async def list_messages(
        self,
        conversation_id: UUID,
        *,
        before_sequence: int | None,
        after_sequence: int | None,
        limit: int,
    ) -> list[AiMessageDocument]:
        filters: dict[str, Any] = {"conversation_id": str(conversation_id)}
        if before_sequence is not None:
            filters["sequence_number"] = {"$lt": before_sequence}
        if after_sequence is not None:
            filters["sequence_number"] = {"$gt": after_sequence}
        descending = after_sequence is None
        cursor = (
            self.database[MongoCollection.AI_MESSAGES.value]
            .find(filters)
            .sort("sequence_number", -1 if descending else 1)
            .limit(max(1, min(limit, 100)))
        )
        documents = [AiMessageDocument.model_validate(item) async for item in cursor]
        return list(reversed(documents)) if descending else documents

    async def message_exists_before(self, conversation_id: UUID, sequence: int) -> bool:
        document = await self.database[MongoCollection.AI_MESSAGES.value].find_one(
            {"conversation_id": str(conversation_id), "sequence_number": {"$lt": sequence}},
            {"_id": 1},
        )
        return document is not None

    async def message_exists_after(self, conversation_id: UUID, sequence: int) -> bool:
        document = await self.database[MongoCollection.AI_MESSAGES.value].find_one(
            {"conversation_id": str(conversation_id), "sequence_number": {"$gt": sequence}},
            {"_id": 1},
        )
        return document is not None

    async def latest_context(self, conversation_id: UUID) -> AiContextSnapshotDocument | None:
        document = await self.database[MongoCollection.AI_CONTEXT_SNAPSHOTS.value].find_one(
            {"conversation_id": str(conversation_id)},
            sort=[("until_sequence", -1)],
        )
        return AiContextSnapshotDocument.model_validate(document) if document else None

    async def upsert_message(self, document: AiMessageDocument) -> None:
        await self.database[MongoCollection.AI_MESSAGES.value].replace_one(
            {"_id": str(document.id)}, document.to_mongo(), upsert=True
        )

    async def upsert_context(self, document: AiContextSnapshotDocument) -> None:
        await self.database[MongoCollection.AI_CONTEXT_SNAPSHOTS.value].replace_one(
            {"_id": str(document.id)}, document.to_mongo(), upsert=True
        )

    async def safe_list_messages(self, *args, **kwargs) -> list[AiMessageDocument] | None:
        if not settings.ai_messages_mongodb_read_enabled:
            return None
        try:
            return await self.list_messages(*args, **kwargs)
        except (MongoUnavailableError, PyMongoError):
            logger.exception("MongoDB message read failed")
            if not settings.ai_messages_sql_fallback_enabled:
                raise
            return None


class SyncConversationDocumentStore:
    """Synchronous canonical message store used by thread-pool services."""

    def __init__(self, manager: SyncMongoManager = sync_mongo_manager, *, database=None) -> None:
        self.manager = manager
        self._database = database

    @property
    def database(self):
        return self._database if self._database is not None else self.manager.database

    @property
    def collection(self):
        return self.database[MongoCollection.AI_MESSAGES.value]

    def upsert(self, document: AiMessageDocument) -> None:
        self.collection.replace_one({"_id": str(document.id)}, document.to_mongo(), upsert=True)

    def get(self, message_id: UUID) -> AiMessageDocument | None:
        item = self.collection.find_one({"_id": str(message_id)})
        return AiMessageDocument.model_validate(item) if item else None

    def by_client_id(
        self, conversation_id: UUID, author_user_id: UUID, client_message_id: UUID
    ) -> AiMessageDocument | None:
        item = self.collection.find_one(
            {
                "conversation_id": str(conversation_id),
                "author_user_id": str(author_user_id),
                "client_message_id": str(client_message_id),
            }
        )
        return AiMessageDocument.model_validate(item) if item else None

    def assistant_by_correlation(
        self, conversation_id: UUID, correlation_id: UUID
    ) -> AiMessageDocument | None:
        item = self.collection.find_one(
            {
                "conversation_id": str(conversation_id),
                "correlation_id": str(correlation_id),
                "role": "assistant",
            }
        )
        return AiMessageDocument.model_validate(item) if item else None

    def list_messages(
        self,
        conversation_id: UUID,
        *,
        before_sequence: int | None,
        after_sequence: int | None,
        limit: int,
    ) -> list[AiMessageDocument]:
        filters: dict[str, Any] = {"conversation_id": str(conversation_id)}
        if before_sequence is not None:
            filters["sequence_number"] = {"$lt": before_sequence}
        if after_sequence is not None:
            filters["sequence_number"] = {"$gt": after_sequence}
        descending = after_sequence is None
        items = list(
            self.collection.find(filters)
            .sort("sequence_number", -1 if descending else 1)
            .limit(max(1, min(limit, 100)))
        )
        documents = [AiMessageDocument.model_validate(item) for item in items]
        return list(reversed(documents)) if descending else documents

    def exists_before(self, conversation_id: UUID, sequence: int) -> bool:
        return (
            self.collection.find_one(
                {
                    "conversation_id": str(conversation_id),
                    "sequence_number": {"$lt": sequence},
                },
                {"_id": 1},
            )
            is not None
        )

    def exists_after(self, conversation_id: UUID, sequence: int) -> bool:
        return (
            self.collection.find_one(
                {
                    "conversation_id": str(conversation_id),
                    "sequence_number": {"$gt": sequence},
                },
                {"_id": 1},
            )
            is not None
        )

    async def safe_message_exists_before(self, conversation_id: UUID, sequence: int) -> bool:
        try:
            return await self.message_exists_before(conversation_id, sequence)
        except (MongoUnavailableError, PyMongoError):
            if not settings.ai_messages_sql_fallback_enabled:
                raise
            return False

    async def safe_message_exists_after(self, conversation_id: UUID, sequence: int) -> bool:
        try:
            return await self.message_exists_after(conversation_id, sequence)
        except (MongoUnavailableError, PyMongoError):
            if not settings.ai_messages_sql_fallback_enabled:
                raise
            return False

    async def safe_latest_context(self, conversation_id: UUID) -> AiContextSnapshotDocument | None:
        if not settings.ai_messages_mongodb_read_enabled:
            return None
        try:
            return await self.latest_context(conversation_id)
        except (MongoUnavailableError, PyMongoError):
            if not settings.ai_messages_sql_fallback_enabled:
                raise
            return None
