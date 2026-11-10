"""Pruebas del consumidor de registro y de la IA proactiva (V2.1)."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import fakeredis
import pytest

from app.core.changelog.consumidor import ConsumidorRegistroCambios
from app.core.changelog.contratos import EntradaRegistroCambios
from app.core.config.configuracion import settings
from app.core.redis.cliente import clave_redis, establecer_cliente_prueba
from app.modules.asistente_proyecto.models import ConversacionIA, RecomendacionIA
from app.modules.asistente_proyecto.services.servicio_asesor_proactivo import (
    _MEMORY_COOLDOWN,
    _MEMORY_PENDING,
    ServicioAsesorProactivo,
)
from app.modules.modelado_uml.engine.modelo_interno import (
    ModeloAtributoUML,
    ModeloClaseUML,
    ModeloDiagramaUML,
)
from app.modules.modelado_uml.models import AtributoUML, ClaseUML, DiagramaUML


@pytest.fixture
def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    establecer_cliente_prueba(client, None)
    _MEMORY_PENDING.clear()
    _MEMORY_COOLDOWN.clear()
    yield client
    establecer_cliente_prueba(None, None)
    _MEMORY_PENDING.clear()
    _MEMORY_COOLDOWN.clear()


class FakeSession:
    def __init__(self, diagram: DiagramaUML, classes: list[ClaseUML], conversation: ConversacionIA | None = None):
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
        if model == DiagramaUML and self.diagram and self.diagram.id == ident:
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
        if "recomendaciones_ia" in q_str:
            return Result([item for item in self.added if isinstance(item, RecomendacionIA) and item.status == "open"])
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


def _make_conversation(project_id: UUID) -> ConversacionIA:
    return ConversacionIA(
        id=uuid4(),
        project_id=project_id,
        title="Chat Equipo",
        last_message_sequence=0,
    )


def _make_diagram(project_id: UUID, diagram_id: UUID) -> DiagramaUML:
    return DiagramaUML(
        id=diagram_id,
        project_id=project_id,
        name="Principal",
        diagram_type="class",
        status="active",
        current_version=1,
        description="",
        metadata_json={},
    )


def _make_class(diagram_id: UUID, name: str, attributes: list[AtributoUML] | None = None) -> ClaseUML:
    cls = ClaseUML(
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


def _make_attr(name: str, data_type: str = "String") -> AtributoUML:
    return AtributoUML(
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


def _load_diagram_model(session: FakeSession, _diagram_id: UUID) -> ModeloDiagramaUML:
    return ModeloDiagramaUML(
        id=str(session.diagram.id),
        project_id=str(session.diagram.project_id),
        name=session.diagram.name,
        classes=[
            ModeloClaseUML(
                id=str(uml_class.id),
                name=uml_class.name,
                visibility=uml_class.visibility,
                attributes=[
                    ModeloAtributoUML(
                        id=str(attribute.id),
                        name=attribute.name,
                        data_type=attribute.data_type,
                        visibility=attribute.visibility,
                    )
                    for attribute in uml_class.attributes
                ],
            )
            for uml_class in session.classes
        ],
    )


def _make_entry(
    project_id: UUID,
    action: str = "CREATE_CLASS",
    source: str = "ui",
    actor_id: UUID | None = None,
    diagram_id: UUID | None = None,
) -> EntradaRegistroCambios:
    return EntradaRegistroCambios(
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
    advisor = ServicioAsesorProactivo(
        db_factory=lambda: session,
        diagram_model_loader=_load_diagram_model,
    )

    with patch.object(settings, "ai_proactive_min_changes", 5), \
         patch.object(advisor, "_publish", new_callable=AsyncMock) as mock_pub:

        # 4 cambios
        for _ in range(4):
            asyncio.run(advisor.al_cambiar(_make_entry(project_id, diagram_id=diagram_id, actor_id=actor_id)))

        # No debe haber publicado nada
        assert mock_pub.await_count == 0

        # 5to cambio
        asyncio.run(advisor.al_cambiar(_make_entry(project_id, diagram_id=diagram_id, actor_id=actor_id)))

        # Ahora sí debe publicar mensaje proactivo y recomendaciones
        assert mock_pub.await_count == 1
        published = mock_pub.await_args.kwargs
        assert published["trigger"] == "min_changes"
        assert len(published["recommendations"]) >= 1


def test_during_cooldown_another_five_changes_do_not_publish(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    empty_class = _make_class(diagram_id, "Factura", attributes=[])
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [empty_class], conv)
    advisor = ServicioAsesorProactivo(
        db_factory=lambda: session,
        diagram_model_loader=_load_diagram_model,
    )

    with patch.object(settings, "ai_proactive_min_changes", 5), \
         patch.object(settings, "ai_proactive_cooldown_seconds", 120), \
         patch.object(advisor, "_publish", new_callable=AsyncMock) as mock_pub:

        # Disparar 5 cambios -> 1er mensaje publicado
        for _ in range(5):
            asyncio.run(advisor.al_cambiar(_make_entry(project_id, diagram_id=diagram_id)))

        assert mock_pub.await_count == 1
        fake_redis.set(clave_redis("proactive", "cooldown", str(project_id)), "1", ex=120)

        # Otros 5 cambios inmediatamente (en cooldown)
        for _ in range(5):
            asyncio.run(advisor.al_cambiar(_make_entry(project_id, diagram_id=diagram_id)))

        # No se publicó un segundo mensaje
        assert mock_pub.await_count == 1


def test_diagram_without_findings_does_not_publish(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    # Clase con atributo válido -> validate_internal_model no genera recomendaciones
    valid_attr = _make_attr("total", "Double")
    valid_class = _make_class(diagram_id, "Factura", attributes=[valid_attr])
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [valid_class], conv)
    advisor = ServicioAsesorProactivo(
        db_factory=lambda: session,
        diagram_model_loader=_load_diagram_model,
    )

    with patch.object(settings, "ai_proactive_min_changes", 5), \
         patch.object(advisor, "_publish", new_callable=AsyncMock) as mock_pub:

        for _ in range(5):
            asyncio.run(advisor.al_cambiar(_make_entry(project_id, diagram_id=diagram_id)))

        assert mock_pub.await_count == 0


def test_same_open_design_recommendation_is_not_published_again(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()
    diagram = _make_diagram(project_id, diagram_id)
    session = FakeSession(diagram, [_make_class(diagram_id, "Factura", attributes=[])], _make_conversation(project_id))
    session.add(RecomendacionIA(
        project_id=project_id,
        conversation_id=session.conversation.id,
        source_message_id=uuid4(),
        category="architecture",
        severity="info",
        title="Sugerencia de diseño",
        description="Agregar atributos a Factura.",
        references_json=[],
        status="open",
    ))
    advisor = ServicioAsesorProactivo(db_factory=lambda: session, diagram_model_loader=_load_diagram_model)
    with patch.object(settings, "ai_proactive_min_changes", 5), patch.object(advisor, "_publish", new_callable=AsyncMock) as published:
        for _ in range(6):
            asyncio.run(advisor.al_cambiar(_make_entry(project_id, diagram_id=diagram_id)))
    assert published.await_count == 0


def test_system_source_is_ignored_ai_counts_as_team(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    empty_class = _make_class(diagram_id, "Factura", attributes=[])
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [empty_class], conv)
    advisor = ServicioAsesorProactivo(
        db_factory=lambda: session,
        diagram_model_loader=_load_diagram_model,
    )

    with patch.object(settings, "ai_proactive_min_changes", 5), \
         patch.object(advisor, "_publish", new_callable=AsyncMock) as mock_pub:

        # 5 cambios con source='system' -> ignorados por completo
        for _ in range(5):
            asyncio.run(advisor.al_cambiar(_make_entry(project_id, source="system", diagram_id=diagram_id)))

        assert mock_pub.await_count == 0

        # 5 cambios con source='ai' -> cuentan como cambios del equipo
        for _ in range(5):
            asyncio.run(advisor.al_cambiar(_make_entry(project_id, source="ai", diagram_id=diagram_id)))

        assert mock_pub.await_count == 1


def test_create_project_version_generates_summary(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [], conv)
    advisor = ServicioAsesorProactivo(
        db_factory=lambda: session,
        diagram_model_loader=_load_diagram_model,
    )

    entry = _make_entry(project_id, action="CREATE_PROJECT_VERSION", diagram_id=diagram_id)

    with patch.object(advisor, "_resumen_version", return_value="Resumen de versión: Ana creó Factura."), \
         patch.object(advisor, "_publish", new_callable=AsyncMock) as mock_pub:

        asyncio.run(advisor.al_cambiar(entry))

        assert mock_pub.await_count == 1
        published = mock_pub.await_args.kwargs
        assert published["trigger"] == "version"
        assert "Resumen de versión" in published["content"]


def test_import_xmi_triggers_on_findings(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    empty_class = _make_class(diagram_id, "Factura", attributes=[])
    conv = _make_conversation(project_id)

    session = FakeSession(diagram, [empty_class], conv)
    advisor = ServicioAsesorProactivo(
        db_factory=lambda: session,
        diagram_model_loader=_load_diagram_model,
    )

    entry = _make_entry(project_id, action="IMPORT_XMI", diagram_id=diagram_id)

    with patch.object(advisor, "_publish", new_callable=AsyncMock) as mock_pub:
        asyncio.run(advisor.al_cambiar(entry))

        assert mock_pub.await_count == 1
        assert mock_pub.await_args.kwargs["trigger"] == "import"


def test_project_without_conversation_logs_and_does_not_fail(fake_redis):
    project_id = uuid4()
    diagram_id = uuid4()

    diagram = _make_diagram(project_id, diagram_id)
    empty_class = _make_class(diagram_id, "Factura", attributes=[])

    # session SIN conversación (conv = None)
    session = FakeSession(diagram, [empty_class], conversation=None)
    advisor = ServicioAsesorProactivo(
        db_factory=lambda: session,
        diagram_model_loader=_load_diagram_model,
    )

    with patch.object(settings, "ai_proactive_min_changes", 1), \
         patch("app.modules.asistente_proyecto.services.servicio_asesor_proactivo.PublicadorEventosIAProyecto.publicar_persistido", new_callable=AsyncMock) as mock_pub:

        # No debe lanzar excepción
        asyncio.run(advisor.al_cambiar(_make_entry(project_id, diagram_id=diagram_id)))
        assert mock_pub.await_count == 0


def test_consumer_xack_and_broadcast(fake_redis):
    project_id = uuid4()
    actor_id = uuid4()
    global_stream = clave_redis("changelog", "all")

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
    consumer = ConsumidorRegistroCambios(advisor=advisor_mock)

    stop_event = asyncio.Event()

    async def stop_later():
        await asyncio.sleep(0.1)
        stop_event.set()

    with patch("app.websocket.gestor_conexiones.manager.broadcast", new_callable=AsyncMock) as mock_broadcast, \
         patch.object(consumer, "_resolve_actor_name", return_value="Ana Dev"):

        async def _run_test():
            await asyncio.gather(consumer.run(stop_event), stop_later())

        asyncio.run(_run_test())

        assert advisor_mock.al_cambiar.await_count >= 1
        assert mock_broadcast.await_count >= 1

        call_args = mock_broadcast.await_args[0]
        assert call_args[0] == str(project_id)
        assert call_args[1]["type"] == "CHANGE_LOGGED"
        assert call_args[1]["payload"]["actor_display_name"] == "Ana Dev"
