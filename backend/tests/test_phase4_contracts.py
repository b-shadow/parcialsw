from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security.jwt import create_access_token, decode_access_token
from app.core.security.password import hash_password, verify_password
from app.main import app


def test_security_password_and_jwt_contracts() -> None:
    password_hash = hash_password("Password123")
    assert password_hash != "Password123"
    assert verify_password("Password123", password_hash)

    user_id = uuid4()
    token = create_access_token(user_id)
    assert decode_access_token(token) == user_id


def test_health_and_openapi_contracts() -> None:
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok", "component": "backend"}
    assert client.get("/api/v1/acceso-usuarios/health").status_code == 200
    assert client.get("/api/v1/proyectos-colaboracion/health").status_code == 200
    assert client.get("/api/v1/modelado-uml/health").status_code == 200
    assert client.get("/api/v1/generacion-software/health").status_code == 200

    paths = client.get("/openapi.json").json()["paths"]
    expected_paths = {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/me",
        "/api/v1/users",
        "/api/v1/projects",
        "/api/v1/projects/{project_id}",
        "/api/v1/projects/{project_id}/members",
        "/api/v1/projects/{project_id}/versions",
        "/api/v1/uml/diagrams",
        "/api/v1/uml/projects/{project_id}/diagrams",
        "/api/v1/uml/diagrams/{diagram_id}/classes",
        "/api/v1/uml/classes/{class_id}/attributes",
        "/api/v1/uml/classes/{class_id}/methods",
        "/api/v1/uml/diagrams/{diagram_id}/relationships",
        "/api/v1/uml/diagrams/{diagram_id}/validate",
        "/api/v1/generation/transformations",
        "/api/v1/generation/spring-boot",
        "/api/v1/generation/flutter",
    }
    assert expected_paths.issubset(paths.keys())


def test_project_websocket_contract() -> None:
    client = TestClient(app)
    project_id = str(uuid4())

    with client.websocket_connect(f"/ws/projects/{project_id}") as websocket:
        assert websocket.receive_json()["type"] == "SESSION_CONNECTED"
        websocket.send_json({"type": "CREATE_CLASS", "payload": {"name": "Usuario"}})
        broadcast = websocket.receive_json()
        ack = websocket.receive_json()
        assert broadcast["type"] == "UML_EVENT"
        assert broadcast["project_id"] == project_id
        assert ack == {"type": "EVENT_ACK", "project_id": project_id}

