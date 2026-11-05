import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config.configuracion import settings
from app.core.nosql.cliente import EstadoMongo
from app.core.nosql.contratos import ColeccionMongo, DocumentoMensajeIA
from app.core.nosql.errores import ErrorMongoNoDisponible
from app.main import app
from app.modules.asistente_proyecto.models import MensajeIA
from app.modules.asistente_proyecto.services.almacen_documentos_conversacion import (
    AlmacenDocumentosConversacion,
    AlmacenSincronoDocumentosConversacion,
    documento_instantanea_contexto,
    documento_mensaje_desde_sql,
    encolar_documento_mensaje,
    hash_contenido_mensaje,
)
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente


def _sql_message(*, sequence: int = 1, content: str = "Analiza el modelo") -> MensajeIA:
    now = datetime.now(UTC)
    return MensajeIA(
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

    document = documento_mensaje_desde_sql(message)
    stored = document.to_mongo()

    assert document.id == message.id
    assert document.status == "completed"
    assert document.detected_intents == ["review_uml"]
    assert document.references_json == message.references_json
    assert document.metadata_json == {"surface": "desktop"}
    assert document.content_hash == hash_contenido_mensaje(message)
    assert DocumentoMensajeIA.model_validate(stored) == document


def test_async_conversation_store_exposes_context_and_cursor_reads() -> None:
    store = AlmacenDocumentosConversacion(database={})
    conversation_id = uuid4()
    store.obtener_contexto_reciente = AsyncMock(return_value=None)
    store.existe_mensaje_anterior = AsyncMock(return_value=True)
    store.existe_mensaje_posterior = AsyncMock(return_value=False)

    assert asyncio.run(store.obtener_contexto_reciente_seguro(conversation_id)) is None
    assert asyncio.run(store.existe_mensaje_anterior_seguro(conversation_id, 2)) is True
    assert asyncio.run(store.existe_mensaje_posterior_seguro(conversation_id, 2)) is False
    assert not hasattr(AlmacenSincronoDocumentosConversacion, "obtener_contexto_reciente_seguro")


def test_missing_mongodb_history_is_reported_instead_of_shown_as_empty() -> None:
    service = ServicioContratoAsistente.__new__(ServicioContratoAsistente)
    service.obtener_conversacion = MagicMock(
        return_value=SimpleNamespace(id=uuid4(), last_message_sequence=16)
    )
    service.repository = MagicMock()
    service.documents = MagicMock()
    service.documents.listar_mensajes_seguro = AsyncMock(return_value=[])

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            service.listar_mensajes(
                uuid4(), uuid4(), before_sequence=None,
                after_sequence=None, limit=20,
            )
        )

    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "CONVERSATION_MESSAGES_MISSING"


@pytest.mark.parametrize("sequences", [[1, 3], [1, 2]])
def test_incomplete_mongodb_history_is_not_shown_as_complete(sequences) -> None:
    service = ServicioContratoAsistente.__new__(ServicioContratoAsistente)
    service.obtener_conversacion = MagicMock(
        return_value=SimpleNamespace(id=uuid4(), last_message_sequence=3)
    )
    service.repository = MagicMock()
    service.documents = MagicMock()
    service.documents.listar_mensajes_seguro = AsyncMock(
        return_value=[SimpleNamespace(sequence_number=value) for value in sequences]
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            service.listar_mensajes(
                uuid4(), uuid4(), before_sequence=None,
                after_sequence=None, limit=20,
            )
        )

    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "CONVERSATION_MESSAGES_MISSING"


def test_phase11_message_write_enqueues_full_document_without_committing() -> None:
    session = MagicMock()
    message = _sql_message()

    document = encolar_documento_mensaje(session, message)

    session.flush.assert_called_once()
    session.commit.assert_not_called()
    event = session.add.call_args.args[0]
    assert event.aggregate_id == message.id
    assert event.payload["collection"] == ColeccionMongo.AI_MESSAGES.value
    assert event.payload["document"]["content_hash"] == document.content_hash


def test_phase11_effective_read_prefers_mongo_and_overlays_pending_sql() -> None:
    first = _sql_message(sequence=1, content="Versión SQL antigua")
    first_document = documento_mensaje_desde_sql(first).model_copy(
        update={"content": "Versión Mongo", "content_hash": "e" * 64}
    )
    pending = _sql_message(sequence=2, content="Pendiente de Outbox")

    effective = ServicioContratoAsistente._mensajes_efectivos(
        [first, pending], [first_document], limit=20, after_sequence=None
    )

    assert [item.sequence_number for item in effective] == [1, 2]
    assert effective[0].content == "Versión Mongo"
    assert effective[1].id == pending.id


def test_phase11_effective_read_keeps_cursor_direction_and_limit() -> None:
    documents = [documento_mensaje_desde_sql(_sql_message(sequence=value)) for value in range(1, 6)]

    forward = ServicioContratoAsistente._mensajes_efectivos([], documents, limit=2, after_sequence=0)
    backward = ServicioContratoAsistente._mensajes_efectivos(
        [], documents, limit=2, after_sequence=None
    )

    assert [item.sequence_number for item in forward] == [1, 2]
    assert [item.sequence_number for item in backward] == [4, 5]


def test_phase11_context_snapshot_id_is_deterministic_and_versioned() -> None:
    conversation = SimpleNamespace(id=uuid4(), project_id=uuid4())
    first = documento_instantanea_contexto(
        conversation,
        summary='{"project_goal":"Ventas"}',
        context={"project_goal": "Ventas"},
        until_sequence=20,
    )
    replay = documento_instantanea_contexto(
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
        document = documento_mensaje_desde_sql(message)
        await asyncio.sleep(0)
        assert hash_contenido_mensaje(document) == document.content_hash

    asyncio.run(scenario())


def test_phase11_sql_fallback_is_reversible(monkeypatch) -> None:
    class UnavailableManager:
        @property
        def database(self):
            raise ErrorMongoNoDisponible("offline")

    store = AlmacenDocumentosConversacion(UnavailableManager())  # type: ignore[arg-type]
    monkeypatch.setattr(settings, "ai_messages_mongodb_read_enabled", True)
    monkeypatch.setattr(settings, "ai_messages_sql_fallback_enabled", True)

    result = asyncio.run(
        store.listar_mensajes_seguro(uuid4(), before_sequence=None, after_sequence=None, limit=20)
    )
    assert result is None

    monkeypatch.setattr(settings, "ai_messages_sql_fallback_enabled", False)
    with pytest.raises(ErrorMongoNoDisponible):
        asyncio.run(
            store.listar_mensajes_seguro(uuid4(), before_sequence=None, after_sequence=None, limit=20)
        )


def test_phase11_readiness_requires_completed_memory_migration(monkeypatch) -> None:
    collection = SimpleNamespace(find_one=AsyncMock(return_value={"status": "completed"}))
    database = {ColeccionMongo.MIGRATION_CHECKPOINTS.value: collection}
    health = EstadoMongo(status="available", required=True, database="case_inteligente_nosql")
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
