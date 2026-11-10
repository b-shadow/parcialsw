from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from ai_engine.orchestration.contratos import (
    IntencionDetectada,
    ResultadoIAUnificado,
    ResultadoOrquestacion,
)
from ai_engine.providers.base import EstadoProveedor
from ai_engine.providers.proveedor_ollama import validar_url_base_ollama
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import UniqueConstraint

from app.core.config.configuracion import settings as app_settings
from app.main import app
from app.modules.asistente_proyecto.models import ConversacionIA
from app.modules.asistente_proyecto.repositories.repositorio_asistente import RepositorioAsistente
from app.modules.asistente_proyecto.schemas.esquemas_asistente import (
    CreacionConversacionIA,
    EstadoProveedorIA,
    SolicitudInteraccionIA,
)
from app.modules.asistente_proyecto.services.fabrica_proveedores import (
    obtener_url_ollama,
    resolver_modelo_ollama,
)
from app.modules.asistente_proyecto.services.servicio_aplicacion_ia_proyecto import (
    ServicioAplicacionIAProyecto,
)
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente


def test_phase2_openapi_contracts_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "post" in paths["/api/v1/projects/{project_id}/ai/interactions"]
    assert "get" in paths["/api/v1/projects/{project_id}/ai/provider-health"]
    assert "post" in paths["/api/v1/projects/{project_id}/ai/actions/{action_id}/confirm"]
    assert "post" in paths["/api/v1/projects/{project_id}/ai/actions/{action_id}/reject"]
    assert "get" in paths["/api/v1/projects/{project_id}/ai/conversations"]
    assert "post" in paths["/api/v1/projects/{project_id}/ai/conversations"]
    assert "patch" in paths["/api/v1/projects/{project_id}/ai/conversations/{conversation_id}"]


def test_interaction_contract_normalizes_content_and_bounds_version() -> None:
    request = SolicitudInteraccionIA(client_message_id=uuid4(), content="  revisa el modelo  ")
    assert request.content == "revisa el modelo"
    with pytest.raises(ValidationError):
        SolicitudInteraccionIA(client_message_id=uuid4(), content="revisa", base_diagram_version=-1)


def test_recommendation_id_is_passed_to_inference_without_exposing_it_in_message() -> None:
    recommendation_id = uuid4()
    request = SolicitudInteraccionIA(
        client_message_id=uuid4(),
        content="Corrige los atributos de Pago.",
        recommendation_id=recommendation_id,
    )
    assert str(recommendation_id) not in request.content
    assert request.model_dump(mode="json")["recommendation_id"] == str(recommendation_id)
    assert ServicioAplicacionIAProyecto._texto_para_inferencia(request).endswith(
        f"ID de recomendacion: {recommendation_id}"
    )


def test_project_can_store_multiple_named_conversations() -> None:
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in ConversacionIA.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("project_id",) not in unique_columns
    assert CreacionConversacionIA(title="  Revision de dominio  ").title == "Revision de dominio"
    assert (
        ServicioContratoAsistente._titulo_desde_primer_mensaje(
            "Analiza el diagrama de ventas y recomienda mejoras importantes"
        )
        == "Analiza el diagrama de ventas y recomienda mejoras"
    )


def test_provider_health_contract_does_not_expose_internal_data() -> None:
    response = EstadoProveedorIA(
        provider="ollama",
        available=False,
        selected_model="qwen2.5-coder:7b",
        selected_model_available=False,
        error_code="provider_unavailable",
    )
    assert set(response.model_dump()) == {
        "provider",
        "available",
        "models",
        "selected_model",
        "selected_model_available",
        "latency_ms",
        "error_code",
        "error_message",
        "configured_sources",
        "gemini_configured",
    }


def test_ollama_configuration_rejects_ssrf_destinations() -> None:
    assert validar_url_base_ollama("http://localhost:11434")
    with pytest.raises(ValueError):
        validar_url_base_ollama("http://169.254.169.254/latest/meta-data")


def test_ollama_source_is_shared_per_project_and_isolated_between_projects() -> None:
    project_local_id, project_aws_id, owner_id = uuid4(), uuid4(), uuid4()
    now = datetime.now(UTC)
    projects = {
        project_local_id: SimpleNamespace(id=project_local_id, owner_id=owner_id, created_at=now, updated_at=now, settings={"ai": {"settings_json": {"origen_ollama": "local"}}}),
        project_aws_id: SimpleNamespace(id=project_aws_id, owner_id=owner_id, created_at=now, updated_at=now, settings={"ai": {"settings_json": {"origen_ollama": "aws"}}}),
    }
    repository = RepositorioAsistente(SimpleNamespace(get=lambda _model, project_id: projects[project_id]))
    assert repository.obtener_configuracion(project_local_id).settings_json["origen_ollama"] == "local"
    assert repository.obtener_configuracion(project_aws_id).settings_json["origen_ollama"] == "aws"


def test_ollama_source_uses_only_server_configured_endpoints(monkeypatch) -> None:
    monkeypatch.setattr(app_settings, "app_env", "production")
    monkeypatch.setattr(app_settings, "ollama_local_base_url", None)
    monkeypatch.setattr(app_settings, "ollama_aws_base_url", "http://10.20.11.10:11434")
    assert obtener_url_ollama("local") is None
    assert obtener_url_ollama("aws") == "http://10.20.11.10:11434"
    with pytest.raises(ValueError):
        obtener_url_ollama("http://attacker.example:11434")


def test_ollama_source_rejects_unknown_project_setting() -> None:
    from app.modules.asistente_proyecto.schemas.esquemas_asistente import (
        ActualizacionConfiguracionIAProyecto,
    )

    with pytest.raises(ValidationError):
        ActualizacionConfiguracionIAProyecto(settings_json={"origen_ollama": "otra_maquina"})


def test_existing_project_image_uses_the_project_ollama_source(monkeypatch) -> None:
    from app.modules.generacion_software.routers import ai as routes
    from app.modules.generacion_software.schemas.ai import SolicitudImagenIA

    project_id, user_id = uuid4(), uuid4()
    captured = {}

    class FakeContracts:
        def __init__(self, db):
            assert db == "database"

        def obtener_configuracion(self, requested_project_id, requested_user_id):
            assert (requested_project_id, requested_user_id) == (project_id, user_id)
            return SimpleNamespace(settings_json={"origen_ollama": "aws"})

    class FakeService:
        def imagen_a_uml(self, payload, **kwargs):
            captured.update(kwargs)
            return "resultado"

    monkeypatch.setattr(routes, "ServicioContratoAsistente", FakeContracts)
    monkeypatch.setattr(routes, "ServicioIA", FakeService)
    monkeypatch.setattr(routes, "obtener_url_ollama", lambda source: "http://10.20.11.10:11434" if source == "aws" else None)

    result = routes.imagen_a_uml(
        SolicitudImagenIA(project_id=project_id, description="diagrama"),
        SimpleNamespace(id=user_id),
        "database",
    )
    assert result == "resultado"
    assert captured == {"ollama_base_url": "http://10.20.11.10:11434", "vision_enabled": True}


def test_missing_configured_model_uses_an_installed_local_qwen_model() -> None:
    class FakeProvider:
        async def health(self, requested_model: str) -> EstadoProveedor:
            return EstadoProveedor(
                provider="ollama",
                available=True,
                installed_models=["qwen3-vl:2b-instruct"],
                requested_model=requested_model,
                requested_model_available=False,
            )

    import asyncio

    selected = asyncio.run(resolver_modelo_ollama(FakeProvider(), "qwen2.5-coder:7b"))
    assert selected == "qwen3-vl:2b-instruct"


def test_assistant_resolves_the_only_diagram_from_the_project() -> None:
    project_id = uuid4()
    diagram_id = uuid4()
    service = ServicioAplicacionIAProyecto(Mock())
    service.uml = SimpleNamespace(
        listar_diagramas_por_proyecto=lambda _: [SimpleNamespace(id=diagram_id)]
    )

    assert service._resolver_id_diagrama_proyecto(project_id, None) == diagram_id


def test_assistant_rejects_a_diagram_from_another_project() -> None:
    project_id = uuid4()
    own_diagram_id = uuid4()
    service = ServicioAplicacionIAProyecto(Mock())
    service.uml = SimpleNamespace(
        listar_diagramas_por_proyecto=lambda _: [SimpleNamespace(id=own_diagram_id)]
    )

    with pytest.raises(HTTPException) as error:
        service._resolver_id_diagrama_proyecto(project_id, uuid4())

    assert error.value.status_code == 404
    assert error.value.detail["code"] == "PROJECT_DIAGRAM_NOT_FOUND"


def test_assistant_persists_detected_intent_names_from_orchestrator() -> None:
    project_id, conversation_id, user_id, user_message_id, correlation_id = (
        uuid4() for _ in range(5)
    )
    service = ServicioAplicacionIAProyecto(Mock())
    service.db.scalars.return_value = []
    service.repository = Mock()
    service.contracts = Mock()
    service.repository.obtener_conversacion.return_value = SimpleNamespace(id=conversation_id)
    service.repository.obtener_mensaje_asistente_por_correlacion.return_value = None
    user_message = SimpleNamespace(status="pending", detected_intents=[])
    service.repository.obtener_mensaje.return_value = user_message
    assistant_message = SimpleNamespace(id=uuid4())
    service.contracts.crear_mensaje = Mock(return_value=(assistant_message, True))
    outcome = ResultadoOrquestacion(
        result=ResultadoIAUnificado(
            answer="El diagrama representa inscripciones de estudiantes en cursos.",
            detected_intents=[
                IntencionDetectada(name="review_uml", confidence=0.9, evidence="opinas", order=1),
                IntencionDetectada(name="answer_question", confidence=0.8, evidence="pregunta", order=2),
            ],
            references=[
                {"type": "diagram", "id": str(uuid4()), "label": "Diagrama actual"},
                {"type": "diagram", "id": "no-es-uuid", "label": "Referencia invalida"},
            ],
        ),
        duration_ms=10,
    )

    result = service._persistir_resultado(
        project_id=project_id,
        conversation_id=conversation_id,
        user_id=user_id,
        user_message_id=user_message_id,
        correlation_id=correlation_id,
        diagram_id=None,
        base_diagram_version=None,
        outcome=outcome,
    )

    assert result is assistant_message
    payload = service.contracts.crear_mensaje.call_args.args[2]
    assert payload.detected_intents == ["review_uml", "answer_question"]
    assert len(payload.references) == 1
    assert payload.references[0].label == "Diagrama actual"
    assert user_message.status == "completed"
