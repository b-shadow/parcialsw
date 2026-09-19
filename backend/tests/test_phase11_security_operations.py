from fastapi.testclient import TestClient

from app.main import app


def test_security_headers_and_request_id_are_applied() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "X-Request-ID" in response.headers


def test_phase11_readiness_endpoint_is_registered() -> None:
    assert "/ready" in app.openapi()["paths"]
