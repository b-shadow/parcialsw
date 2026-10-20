"""Pruebas del consumidor de registro y de la IA proactiva (V2.1)."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import fakeredis
import pytest

from app.core.changelog.consumer import ChangeLogConsumer
from app.core.changelog.contracts import ChangeLogEntry
from app.core.config.settings import settings
from app.core.redis.client import redis_key, set_test_client
from app.modules.asistente_proyecto.models import AiConversation, AiMessage, AiRecommendation
from app.modules.asistente_proyecto.services.proactive_advisor_service import (
    ProactiveAdvisorService,
    _MEMORY_COOLDOWN,
    _MEMORY_PENDING,
)
from app.modules.modelado_uml.models import UmlAttribute, UmlClass, UmlDiagram


@pytest.fixture
def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    set_test_client(client, None)
    _MEMORY_PENDING.clear()
    _MEMORY_COOLDOWN.clear()
    yield client
    set_test_client(None, None)
    _MEMORY_PENDING.clear()
    _MEMORY_COOLDOWN.clear()


class FakeSession:
    def __init__(self, diagram: UmlDiagram, classes: list[UmlClass], conversation: AiConversation | None = None):
        self.diagram = diagram
        self.classes = classes
        self.conversation = conversation
        self.added: list[object] = []
        self.info = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, model, ident):
        if model == UmlDiagram and self.diagram and self.diagram.id == ident:
            return self.diagram
        return None

    def scalar(self, query):
        q_str = str(query)
        if "ai_conversations" in q_str:
            return self.conversation
        return None

    def scalars(self, query):
        q_str = str(query)
        class Result:
            def __init__(self, items):
                self._items = items
            def all(self):
                return self._items
            def __iter__(self):
                return iter(self._items)

        if "uml_classes" in q_str:
            return Result(self.classes)
        return Result([])

    def add(self, obj):
        if hasattr(obj, "id") and not obj.id:
            obj.id = uuid4()
        if hasattr(obj, "created_at") and not obj.created_at:
            obj.created_at = datetime.now(UTC)
        if hasattr(obj, "sequence_number") and not obj.sequence_number:
            obj.sequence_number = 1
        if hasattr(obj, "correlation_id") and not obj.correlation_id:
            obj.correlation_id = uuid4()
        self.added.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def _make_conversation(project_id: UUID) -> AiConversation:
    return AiConversation(
        id=uuid4(),
        project_id=project_id,
        title="Chat Equipo",
        last_message_sequence=0,
    )


def _make_diagram(project_id: UUID, diagram_id: UUID) -> UmlDiagram:
    return UmlDiagram(
        id=diagram_id,
        project_id=project_id,
        name="Principal",
        diagram_type="class",
        status="active",
        current_version=1,
        description="",
        metadata_json={},
    )


def _make_class(diagram_id: UUID, name: str, attributes: list[UmlAttribute] | None = None) -> UmlClass:
    cls = UmlClass(
        id=uuid4(),
        diagram_id=diagram_id,
        name=name,
        visibility="public",
        element_type="class",
        stereotype=None,
        description="",
        metadata_json={},
    )
    cls.attributes = attributes or []
    cls.methods = []
    return cls


def _make_attr(name: str, data_type: str = "String") -> UmlAttribute:
    return UmlAttribute(
        id=uuid4(),
        name=name,
        data_type=data_type,
        visibility="private",
        initial_value=None,
        multiplicity=None,
        is_required=False,
        order_index=0,
        constraints={},
    )


def _make_entry(
    project_id: UUID,
    action: str = "CREATE_CLASS",
    source: str = "ui",
    actor_id: UUID | None = None,
    diagram_id: UUID | None = None,
) -> ChangeLogEntry:
    return ChangeLogEntry(
        id=f"1000-{uuid4().hex[:6]}",
        project_id=project_id,
        occurred_at=datetime.now(UTC),
        actor_user_id=actor_id or uuid4(),
        source=source,
        module="modelado_uml",
        action=action,
        summary=f"Usuario ejecutó {action}",
        diagram_id=diagram_id,
        metadata={},
    )


def test_four_changes_do_not_publish_fifth_with_invalid_diagram_publishes(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()
    actor_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    # Clase vacía (sin atributos) provoca recomendación de calidad
    empty_class = _make_class(diagram_id, "Factura", attributes=[])
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [empty_class], conv)
    advisor = ProactiveAdvisorService(db_factory=lambda: session)

    with patch.object(settings, "ai_proactive_min_changes", 5), \
         patch("app.modules.asistente_proyecto.services.proactive_advisor_service.ProjectAiEventPublisher.publish_persisted", new_callable=AsyncMock) as mock_pub:

        # 4 cambios
        for _ in range(4):
            asyncio.run(advisor.on_change(_make_entry(project_id, diagram_id=diagram_id, actor_id=actor_id)))

        # No debe haber publicado nada
        assert mock_pub.await_count == 0
        assert not any(isinstance(x, AiMessage) for x in session.added)

        # 5to cambio
        asyncio.run(advisor.on_change(_make_entry(project_id, diagram_id=diagram_id, actor_id=actor_id)))

        # Ahora sí debe publicar mensaje proactivo y recomendaciones
        messages = [x for x in session.added if isinstance(x, AiMessage)]
        assert len(messages) == 1
        assert messages[0].metadata_json.get("kind") == "proactive"
        assert messages[0].metadata_json.get("trigger") == "min_changes"

        recs = [x for x in session.added if isinstance(x, AiRecommendation)]
        assert len(recs) >= 1
        assert mock_pub.await_count >= 2


def test_during_cooldown_another_five_changes_do_not_publish(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    empty_class = _make_class(diagram_id, "Factura", attributes=[])
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [empty_class], conv)
    advisor = ProactiveAdvisorService(db_factory=lambda: session)

    with patch.object(settings, "ai_proactive_min_changes", 5), \
         patch.object(settings, "ai_proactive_cooldown_seconds", 120), \
         patch("app.modules.asistente_proyecto.services.proactive_advisor_service.ProjectAiEventPublisher.publish_persisted", new_callable=AsyncMock) as mock_pub:

        # Disparar 5 cambios -> 1er mensaje publicado
        for _ in range(5):
            asyncio.run(advisor.on_change(_make_entry(project_id, diagram_id=diagram_id)))

        assert len([x for x in session.added if isinstance(x, AiMessage)]) == 1

        # Otros 5 cambios inmediatamente (en cooldown)
        for _ in range(5):
            asyncio.run(advisor.on_change(_make_entry(project_id, diagram_id=diagram_id)))

        # No se publicó un segundo mensaje
        assert len([x for x in session.added if isinstance(x, AiMessage)]) == 1


def test_diagram_without_findings_does_not_publish(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    # Clase con atributo válido -> validate_internal_model no genera recomendaciones
    valid_attr = _make_attr("total", "Double")
    valid_class = _make_class(diagram_id, "Factura", attributes=[valid_attr])
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [valid_class], conv)
    advisor = ProactiveAdvisorService(db_factory=lambda: session)

    with patch.object(settings, "ai_proactive_min_changes", 5), \
         patch("app.modules.asistente_proyecto.services.proactive_advisor_service.ProjectAiEventPublisher.publish_persisted", new_callable=AsyncMock) as mock_pub:

        for _ in range(5):
            asyncio.run(advisor.on_change(_make_entry(project_id, diagram_id=diagram_id)))

        assert mock_pub.await_count == 0
        assert not any(isinstance(x, AiMessage) for x in session.added)


def test_system_source_is_ignored_ai_counts_as_team(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    empty_class = _make_class(diagram_id, "Factura", attributes=[])
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [empty_class], conv)
    advisor = ProactiveAdvisorService(db_factory=lambda: session)

    with patch.object(settings, "ai_proactive_min_changes", 5), \
         patch("app.modules.asistente_proyecto.services.proactive_advisor_service.ProjectAiEventPublisher.publish_persisted", new_callable=AsyncMock) as mock_pub:

        # 5 cambios con source='system' -> ignorados por completo
        for _ in range(5):
            asyncio.run(advisor.on_change(_make_entry(project_id, source="system", diagram_id=diagram_id)))

        assert mock_pub.await_count == 0

        # 5 cambios con source='ai' -> cuentan como cambios del equipo
        for _ in range(5):
            asyncio.run(advisor.on_change(_make_entry(project_id, source="ai", diagram_id=diagram_id)))

        assert mock_pub.await_count >= 2


def test_create_project_version_generates_summary(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [], conv)
    advisor = ProactiveAdvisorService(db_factory=lambda: session)

    entry = _make_entry(project_id, action="CREATE_PROJECT_VERSION", diagram_id=diagram_id)

    with patch.object(advisor, "_version_summary", return_value="Resumen de versión: Ana creó Factura."), \
         patch("app.modules.asistente_proyecto.services.proactive_advisor_service.ProjectAiEventPublisher.publish_persisted", new_callable=AsyncMock) as mock_pub:

        asyncio.run(advisor.on_change(entry))

        messages = [x for x in session.added if isinstance(x, AiMessage)]
        assert len(messages) == 1
        assert messages[0].metadata_json.get("trigger") == "version"
        assert "Resumen de versión" in messages[0].content


def test_import_xmi_triggers_on_findings(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    empty_class = _make_class(diagram_id, "Factura", attributes=[])
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [empty_class], conv)
    advisor = ProactiveAdvisorService(db_factory=lambda: session)

    entry = _make_entry(project_id, action="IMPORT_XMI", diagram_id=diagram_id)

    with patch("app.modules.asistente_proyecto.services.proactive_advisor_service.ProjectAiEventPublisher.publish_persisted", new_callable=AsyncMock) as mock_pub:
        asyncio.run(advisor.on_change(entry))

        messages = [x for x in session.added if isinstance(x, AiMessage)]
        assert len(messages) == 1
        assert messages[0].metadata_json.get("trigger") == "import"


def test_project_without_conversation_logs_and_does_not_fail(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    empty_class = _make_class(diagram_id, "Factura", attributes=[])

    # session SIN conversación (conv = None)
    session = FakeSession(diagram, [empty_class], conversation=None)
    advisor = ProactiveAdvisorService(db_factory=lambda: session)

    with patch.object(settings, "ai_proactive_min_changes", 1), \
         patch("app.modules.asistente_proyecto.services.proactive_advisor_service.ProjectAiEventPublisher.publish_persisted", new_callable=AsyncMock) as mock_pub:

        # No debe lanzar excepción
        asyncio.run(advisor.on_change(_make_entry(project_id, diagram_id=diagram_id)))
        assert mock_pub.await_count == 0


def test_consumer_xack_and_broadcast(fake_redis):
    project_id = uuid4()
    actor_id = uuid4()
    global_stream = redis_key("changelog", "all")

    # Insertar mensaje en Redis Stream global
    payload = {
        "project_id": str(project_id),
        "occurred_at": datetime.now(UTC).isoformat(),
        "actor_user_id": str(actor_id),
        "source": "ui",
        "module": "modelado_uml",
        "action": "CREATE_CLASS",
        "summary": "Ana creó Factura",
        "metadata": "{}",
    }
    fake_redis.xadd(global_stream, payload)

    advisor_mock = AsyncMock()
    consumer = ChangeLogConsumer(advisor=advisor_mock)

    stop_event = asyncio.Event()

    async def stop_later():
        await asyncio.sleep(0.1)
        stop_event.set()

    with patch("app.websocket.connection_manager.manager.broadcast", new_callable=AsyncMock) as mock_broadcast, \
         patch.object(consumer, "_resolve_actor_name", return_value="Ana Dev"):

        async def _run_test():
            await asyncio.gather(consumer.run(stop_event), stop_later())

        asyncio.run(_run_test())

        assert advisor_mock.on_change.await_count >= 1
        assert mock_broadcast.await_count >= 1

        call_args = mock_broadcast.await_args[0]
        assert call_args[0] == str(project_id)
        assert call_args[1]["type"] == "CHANGE_LOGGED"
        assert call_args[1]["payload"]["actor_display_name"] == "Ana Dev"
