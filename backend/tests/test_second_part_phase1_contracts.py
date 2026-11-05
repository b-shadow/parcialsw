from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.main import app
from app.modules.asistente_proyecto.schemas.esquemas_asistente import (
    ActualizacionConfiguracionIAProyecto,
)
from app.modules.asistente_proyecto.schemas.eventos_websocket import (
    ActorWebSocketV2,
    EventoWebSocketV2,
)
from app.modules.modelado_uml.engine.modelo_interno import ModeloMetodoUML
from app.modules.modelado_uml.schemas.especificacion_metodo import (
    CreacionEspecificacionMetodoUML,
)
from app.modules.proyectos_colaboracion.schemas.instantanea import (
    InstantaneaProyecto,
    InstantaneaProyectoV2,
    analizar_instantanea_proyecto,
)


def test_phase1_second_part_openapi_contracts_are_registered() -> None:
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/uml/methods/{method_id}/specification": {"get", "put", "patch"},
        "/api/v1/projects/{project_id}/ai/settings": {"get", "put"},
        "/api/v1/projects/{project_id}/ai/conversation": {"get"},
        "/api/v1/projects/{project_id}/ai/messages": {"get"},
        "/api/v1/projects/{project_id}/ai/actions": {"get"},
        "/api/v1/projects/{project_id}/ai/recommendations": {"get"},
        "/api/v1/projects/{project_id}/ai/interactions": {"post"},
        "/api/v1/projects/{project_id}/ai/provider-health": {"get"},
        "/api/v1/projects/{project_id}/ai/actions/{action_id}/confirm": {"post"},
        "/api/v1/projects/{project_id}/ai/actions/{action_id}/reject": {"post"},
        "/api/v1/projects/{project_id}/flutter-theme": {"get", "put"},
        "/api/v1/mobile/projects": {"get"},
        "/api/v1/mobile/projects/{project_id}/diagrams": {"get"},
        "/api/v1/mobile/diagrams/{diagram_id}": {"get"},
    }
    for path, methods in expected.items():
        assert path in paths
        assert methods <= set(paths[path])


def test_method_specification_normalizes_rules_and_allows_incomplete_drafts() -> None:
    specification = CreacionEspecificacionMetodoUML(
        exposure="user_action",
        preconditions=["El estudiante debe existir"],
        backend_contract={"http_method": "POST", "path": "/inscripciones"},
        frontend_contract={
            "interaction": "form",
            "label": "Inscribir estudiante",
            "fields": [],
        },
    )
    assert specification.preconditions[0].code == "el_estudiante_debe_existir"

    draft = CreacionEspecificacionMetodoUML(exposure="user_action")
    assert draft.backend_contract is None
    assert draft.frontend_contract is None
    with pytest.raises(ValidationError):
        CreacionEspecificacionMetodoUML(
            exposure="api",
            backend_contract={"http_method": "POST", "path": "sin-barra"},
        )


def test_ai_settings_reject_nested_secrets() -> None:
    with pytest.raises(ValidationError):
        ActualizacionConfiguracionIAProyecto(settings_json={"runtime": {"api_token": "not-allowed"}})


def test_snapshot_v1_is_adapted_and_future_versions_are_rejected() -> None:
    project = InstantaneaProyecto(id=uuid4(), name="Ventas")
    adapted = analizar_instantanea_proyecto({"diagrams": []}, project)
    assert adapted.schema_version == 2
    assert adapted.project.id == project.id
    assert adapted.flutter_theme is None

    with pytest.raises(ValueError, match="no soportada"):
        analizar_instantanea_proyecto({"schema_version": 99}, project)


def test_snapshot_removes_sensitive_generation_settings() -> None:
    snapshot = InstantaneaProyectoV2(
        captured_at=datetime.now(UTC),
        project=InstantaneaProyecto(id=uuid4(), name="Ventas"),
        generation_settings={
            "target": "flutter",
            "runtime": {"api_token": "secret-value", "port": 8080},
        },
    )
    assert snapshot.generation_settings == {
        "target": "flutter",
        "runtime": {"port": 8080},
    }


def test_websocket_v2_is_typed_and_serializable() -> None:
    event = EventoWebSocketV2(
        type="AI_MESSAGE_CREATED",
        event_id=uuid4(),
        project_id=uuid4(),
        sequence_number=1,
        correlation_id=uuid4(),
        occurred_at=datetime.now(UTC),
        actor=ActorWebSocketV2(display_name="Editor UML"),
        payload={"message_id": str(uuid4())},
    )
    serialized = event.model_dump(mode="json")
    assert serialized["protocol_version"] == 2
    assert serialized["type"] == "AI_MESSAGE_CREATED"


def test_internal_method_model_keeps_optional_specification_compatibility() -> None:
    legacy = ModeloMetodoUML(name="calcular", return_type="double")
    assert legacy.specification is None
    enriched = ModeloMetodoUML(
        name="inscribir",
        specification={"operation_kind": "create", "exposure": "user_action"},
    )
    dumped = enriched.model_dump(mode="json")
    assert dumped["specification"]["operation_kind"] == "create"

