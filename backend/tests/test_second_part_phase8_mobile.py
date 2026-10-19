from ai_engine.context import ContextConstraints
from fastapi.testclient import TestClient

from app.main import app
from app.modules.asistente_proyecto.schemas.assistant import RequestedContext
from app.modules.proyectos_colaboracion.schemas.mobile import MobileDiagramDetail


def test_mobile_diagram_contract_is_always_read_only() -> None:
    schema = MobileDiagramDetail.model_json_schema()
    assert schema["properties"]["can_edit"]["default"] is False


def test_phase8_mobile_routes_are_exposed() -> None:
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    expected = {
        "/api/v1/mobile/projects",
        "/api/v1/mobile/projects/{project_id}/diagrams",
        "/api/v1/mobile/diagrams/{diagram_id}",
        "/api/v1/mobile/projects/{project_id}/generations",
    }
    assert expected <= set(paths)


def test_mobile_surface_exposes_no_mutating_method() -> None:
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    mobile_operations = {
        method
        for path, operations in paths.items()
        if path.startswith("/api/v1/mobile/")
        for method in operations
        if method in {"post", "put", "patch", "delete"}
    }
    assert mobile_operations == set()


def test_mobile_ai_surface_reaches_shared_context_contract() -> None:
    request = RequestedContext(surface="mobile_readonly")
    constraints = ContextConstraints(surface=request.surface)
    assert constraints.surface == "mobile_readonly"
