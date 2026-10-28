import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config.settings import settings
from app.core.nosql.client import MongoHealth
from app.core.nosql.contracts import AiMessageDocument, MongoCollection
from app.core.nosql.errors import MongoUnavailableError
from app.main import app
from app.modules.asistente_proyecto.models import AiMessage
from app.modules.asistente_proyecto.services.assistant_service import AssistantContractService
from app.modules.asistente_proyecto.services.conversation_document_store import (
    ConversationDocumentStore,
    context_snapshot_document,
    enqueue_message_document,
    message_content_hash,
    message_document_from_sql,
)


def _sql_message(*, sequence: int = 1, content: str = "Analiza el modelo") -> AiMessage:
    now = datetime.now(UTC)
    return AiMessage(
        id=uuid4(),
        conversation_id=uuid4(),
        project_id=uuid4(),
        author_user_id=uuid4(),
        role="user",
        content=content,
        sequence_number=sequence,
        client_message_id=uuid4(),
        correlation_id=uuid4(),
        status="completed",
        detected_intents=["review_uml"],
        references_json=[{"type": "project", "id": str(uuid4()), "label": "Proyecto"}],
        metadata_json={"surface": "desktop"},
        created_at=now,
        updated_at=now,
    )


def test_phase11_message_document_preserves_public_contract_and_hash() -> None:
    message = _sql_message()

    document = message_document_from_sql(message)
    stored = document.to_mongo()

    assert document.id == message.id
    assert document.status == "completed"
    assert document.detected_intents == ["review_uml"]
    assert document.references_json == message.references_json
    assert document.metadata_json == {"surface": "desktop"}
    assert document.content_hash == message_content_hash(message)
    assert AiMessageDocument.model_validate(stored) == document


def test_phase11_message_write_enqueues_full_document_without_committing() -> None:
    session = MagicMock()
    message = _sql_message()

    document = enqueue_message_document(session, message)

    session.flush.assert_called_once()
    session.commit.assert_not_called()
    event = session.add.call_args.args[0]
    assert event.aggregate_id == message.id
    assert event.payload["collection"] == MongoCollection.AI_MESSAGES.value
    assert event.payload["document"]["content_hash"] == document.content_hash


def test_phase11_effective_read_prefers_mongo_and_overlays_pending_sql() -> None:
    first = _sql_message(sequence=1, content="Versión SQL antigua")
    first_document = message_document_from_sql(first).model_copy(
        update={"content": "Versión Mongo", "content_hash": "e" * 64}
    )
    pending = _sql_message(sequence=2, content="Pendiente de Outbox")

    effective = AssistantContractService._effective_messages(
        [first, pending], [first_document], limit=20, after_sequence=None
    )

    assert [item.sequence_number for item in effective] == [1, 2]
    assert effective[0].content == "Versión Mongo"
    assert effective[1].id == pending.id


def test_phase11_effective_read_keeps_cursor_direction_and_limit() -> None:
    documents = [message_document_from_sql(_sql_message(sequence=value)) for value in range(1, 6)]

    forward = AssistantContractService._effective_messages([], documents, limit=2, after_sequence=0)
    backward = AssistantContractService._effective_messages(
        [], documents, limit=2, after_sequence=None
    )

    assert [item.sequence_number for item in forward] == [1, 2]
    assert [item.sequence_number for item in backward] == [4, 5]


def test_phase11_context_snapshot_id_is_deterministic_and_versioned() -> None:
    conversation = SimpleNamespace(id=uuid4(), project_id=uuid4())
    first = context_snapshot_document(
        conversation,
        summary='{"project_goal":"Ventas"}',
        context={"project_goal": "Ventas"},
        until_sequence=20,
    )
    replay = context_snapshot_document(
        conversation,
        summary='{"project_goal":"Ventas"}',
        context={"project_goal": "Ventas"},
        until_sequence=20,
    )

    assert first.id == replay.id
    assert first.content_hash == replay.content_hash
    assert first.schema_version == 1


def test_phase11_document_roundtrip_is_async_safe() -> None:
    async def scenario() -> None:
        message = _sql_message()
        document = message_document_from_sql(message)
        await asyncio.sleep(0)
        assert message_content_hash(document) == document.content_hash

    asyncio.run(scenario())


def test_phase11_sql_fallback_is_reversible(monkeypatch) -> None:
    class UnavailableManager:
        @property
        def database(self):
            raise MongoUnavailableError("offline")

    store = ConversationDocumentStore(UnavailableManager())  # type: ignore[arg-type]
    monkeypatch.setattr(settings, "ai_messages_mongodb_read_enabled", True)
    monkeypatch.setattr(settings, "ai_messages_sql_fallback_enabled", True)

    result = asyncio.run(
        store.safe_list_messages(uuid4(), before_sequence=None, after_sequence=None, limit=20)
    )
    assert result is None

    monkeypatch.setattr(settings, "ai_messages_sql_fallback_enabled", False)
    with pytest.raises(MongoUnavailableError):
        asyncio.run(
            store.safe_list_messages(uuid4(), before_sequence=None, after_sequence=None, limit=20)
        )


def test_phase11_readiness_requires_completed_memory_migration(monkeypatch) -> None:
    collection = SimpleNamespace(find_one=AsyncMock(return_value={"status": "completed"}))
    database = {MongoCollection.MIGRATION_CHECKPOINTS.value: collection}
    health = MongoHealth(status="available", required=True, database="case_inteligente_nosql")
    session_factory = MagicMock()
    monkeypatch.setattr(settings, "ai_messages_migration_required", True)

    with (
        patch("app.main.SessionLocal", session_factory),
        patch.object(app.state.mongo_manager, "ping", AsyncMock(return_value=health)),
        patch.object(app.state.mongo_manager, "_database", database),
    ):
        response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json()["components"]["ai_memory_migration"] == {
        "status": "completed",
        "required": True,
    }
