"""Pruebas del proveedor opcional Gemini e integración con la fábrica de proveedores (V1.7)."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from ai_engine.providers.proveedor_gemini import ProveedorGemini

from app.core.config.configuracion import settings
from app.modules.asistente_proyecto.schemas.esquemas_asistente import (
    ActualizacionConfiguracionIAProyecto,
)
from app.modules.asistente_proyecto.services.fabrica_proveedores import (
    obtener_proveedor_gemini,
    seleccionar_proveedor,
)
from app.modules.asistente_proyecto.services.servicio_aplicacion_ia_proyecto import (
    ServicioAplicacionIAProyecto,
)
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente
from app.modules.proyectos_colaboracion.models import IntegranteProyecto, Proyecto


def test_select_provider_gemini_without_api_key_returns_none() -> None:
    with patch.object(settings, "gemini_api_key", None):
        provider, model = asyncio.run(seleccionar_proveedor("gemini"))
        assert provider is None
        assert model == ""


def test_select_provider_gemini_with_api_key_returns_provider() -> None:
    with patch.object(settings, "gemini_api_key", "test-key-123"):
        obtener_proveedor_gemini.cache_clear()
        provider, model = asyncio.run(seleccionar_proveedor("gemini"))
        assert isinstance(provider, ProveedorGemini)
        assert model == "gemini-2.5-flash"


def test_select_provider_rule_engine() -> None:
    provider, model = asyncio.run(seleccionar_proveedor("rule_engine"))
    assert provider is None
    assert model == "deterministic-v2"


def test_provider_health_gemini_without_key_reports_missing_key() -> None:
    project_id = uuid4()
    user_id = uuid4()

    mock_db = Mock()
    service = ServicioAplicacionIAProyecto(mock_db)
    service.contracts = SimpleNamespace(
        obtener_configuracion=lambda pid, uid: SimpleNamespace(
            preferred_provider="gemini",
            model_name="gemini-2.5-flash",
        )
    )

    with patch.object(settings, "gemini_api_key", None):
        health = asyncio.run(service.estado_proveedor(project_id, user_id))
        assert health.provider == "gemini"
        assert health.available is False
        assert health.error_code == "missing_api_key"
        assert health.error_message == "Falta GEMINI_API_KEY"


def test_put_ai_settings_with_gemini_as_organizer() -> None:
    project_id = uuid4()
    user_id = uuid4()

    mock_member = IntegranteProyecto(
        project_id=project_id,
        user_id=user_id,
        project_role="ORGANIZADOR",
    )
    mock_project = Proyecto(
        name="Proyecto Demo",
        owner_id=user_id,
        revision=1,
        settings={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class MockSession:
        def scalar(self, query):
            q_str = str(query)
            if "integrantes_proyecto" in q_str:
                return mock_member
            return mock_project

        def scalars(self, query):
            class Result:
                def all(self):
                    return []
            return Result()

        def get(self, model, ident):
            return mock_project

        def add(self, obj):
            pass

        def commit(self):
            pass

        def flush(self):
            pass

        def refresh(self, obj):
            pass

    mock_db = MockSession()
    service = ServicioContratoAsistente(mock_db)
    service._publish_settings_updated = Mock()

    payload = ActualizacionConfiguracionIAProyecto(
        enabled=True,
        preferred_provider="gemini",
        model_name="gemini-2.5-flash",
    )

    updated = service.actualizar_configuracion(project_id, user_id, payload)
    assert updated.preferred_provider == "gemini"
    assert updated.model_name == "gemini-2.5-flash"
