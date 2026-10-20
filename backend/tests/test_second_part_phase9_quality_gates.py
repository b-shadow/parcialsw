from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config.settings import settings
from app.main import app


def test_phase9_openapi_operation_ids_are_unique() -> None:
    operation_ids = [
        operation["operationId"]
        for path in app.openapi()["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]

    assert operation_ids
    assert len(operation_ids) == len(set(operation_ids))


def test_phase9_allowed_cors_origin_receives_header() -> None:
    origin = settings.cors_origins[0]
    response = TestClient(app).options(
        "/api/v1/projects",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_phase9_unknown_cors_origin_is_not_authorized() -> None:
    response = TestClient(app).options(
        "/api/v1/projects",
        headers={
            "Origin": "https://attacker.invalid",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_phase9_readiness_uses_503_when_database_is_unavailable() -> None:
    with patch("app.main.SessionLocal") as session_factory:
        session_factory.return_value.__enter__.return_value.execute.side_effect = OperationalError(
            "SELECT 1", {}, Exception("database unavailable")
        )
        response = TestClient(app).get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}
