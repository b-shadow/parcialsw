"""Registro, inicio de sesión y proyecto con JSON público en español."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config.configuracion import settings
from app.main import app

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("MONGODB_TEST_URI"),
    reason="Se requieren PostgreSQL y MongoDB aislados",
)


def test_flujo_http_real_con_nombres_json_espanoles() -> None:
    assert settings.database_url.rsplit("/", 1)[-1].endswith("test")
    assert settings.mongodb_database.endswith("test")
    cabeceras = {"X-Contrato-Idioma": "es"}
    correo = f"contrato-{uuid4()}@example.com"
    with TestClient(app) as client:
        alta = client.post(
            "/api/v1/auth/register",
            json={"nombre_completo": "Prueba Contrato", "correo": correo, "contrasena": "clave-segura-123"},
            headers=cabeceras,
        )
        assert alta.status_code == 201, alta.text
        assert alta.json()["correo"] == correo

        acceso = client.post(
            "/api/v1/auth/login",
            json={"correo": correo, "contrasena": "clave-segura-123"},
            headers=cabeceras,
        )
        assert acceso.status_code == 200, acceso.text
        token = acceso.json()["token_acceso"]
        autorizadas = {**cabeceras, "Authorization": f"Bearer {token}"}

        creado = client.post(
            "/api/v1/projects",
            json={"nombre": "Proyecto en español", "descripcion": "Prueba de contrato"},
            headers=autorizadas,
        )
        assert creado.status_code == 201, creado.text
        proyecto = creado.json()
        assert proyecto["nombre"] == "Proyecto en español"
        assert "propietario_id" in proyecto and "configuracion" in proyecto
        assert "owner_id" not in proyecto and "settings" not in proyecto

        listado = client.get("/api/v1/projects", headers=autorizadas)
        assert listado.status_code == 200
        assert any(item["id"] == proyecto["id"] for item in listado.json())

        with client.websocket_connect(
            f"/ws/projects/{proyecto['id']}?contrato=es",
            subprotocols=["case-v1", f"case-auth.{token}"],
        ) as websocket:
            bienvenida = websocket.receive_json()
            assert bienvenida["tipo"] == "SESSION_CONNECTED"
            assert bienvenida["proyecto_id"] == proyecto["id"]
            assert "project_id" not in bienvenida
