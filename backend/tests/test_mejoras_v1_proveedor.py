"""Pruebas del proveedor opcional Gemini e integración con la fábrica de proveedores (V1.7)."""

import asyncio
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from ai_engine.context import ActorContext, AiProjectContext, ProjectContext
from ai_engine.orchestration.contracts import UnifiedAiResult
from ai_engine.providers.gemini_provider import GeminiProvider
from app.core.config.settings import settings
from app.modules.asistente_proyecto.models import AiProjectSettings
from app.modules.asistente_proyecto.schemas.assistant import (
    AiInteractionRequest,
    AiProjectSettingsUpdate,
)
from app.modules.asistente_proyecto.services.assistant_service import AssistantContractService
from app.modules.asistente_proyecto.services.project_ai_application_service import (
    ProjectAiApplicationService,
)
from app.modules.asistente_proyecto.services.provider_factory import (
    get_gemini_provider,
    select_provider,
)
from app.modules.proyectos_colaboracion.models import Project, ProjectMember


def test_select_provider_gemini_without_api_key_returns_none() -> None:
    with patch.object(settings, "gemini_api_key", None):
        provider, model = asyncio.run(select_provider("gemini"))
        assert provider is None
        assert model == ""


def test_select_provider_gemini_with_api_key_returns_provider() -> None:
    with patch.object(settings, "gemini_api_key", "test-key-123"):
        get_gemini_provider.cache_clear()
        provider, model = asyncio.run(select_provider("gemini"))
        assert isinstance(provider, GeminiProvider)
        assert model == "gemini-2.5-flash"


def test_select_provider_rule_engine() -> None:
    provider, model = asyncio.run(select_provider("rule_engine"))
    assert provider is None
    assert model == "deterministic-v2"


def test_provider_health_gemini_without_key_reports_missing_key() -> None:
    project_id = uuid4()
    user_id = uuid4()

    mock_db = Mock()
    service = ProjectAiApplicationService(mock_db)
    service.contracts = SimpleNamespace(
        get_settings=lambda pid, uid: SimpleNamespace(
            preferred_provider="gemini",
            model_name="gemini-2.5-flash",
        )
    )

    with patch.object(settings, "gemini_api_key", None):
        health = asyncio.run(service.provider_health(project_id, user_id))
        assert health.provider == "gemini"
        assert health.available is False
        assert health.error_code == "missing_api_key"
        assert health.error_message == "Falta GEMINI_API_KEY"


def test_put_ai_settings_with_gemini_as_organizer() -> None:
    project_id = uuid4()
    user_id = uuid4()

    existing_settings = AiProjectSettings(
        project_id=project_id,
        preferred_provider="ollama",
        model_name="qwen2.5-coder:7b",
        created_by_user_id=user_id,
        updated_by_user_id=user_id,
    )

    mock_member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        project_role="ORGANIZADOR",
    )
    mock_project = Project(
        name="Proyecto Demo",
        owner_id=user_id,
        revision=1,
    )

    class MockSession:
        def scalar(self, query):
            q_str = str(query)
            if "project_members" in q_str:
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
    service = AssistantContractService(mock_db)
    service.repository = SimpleNamespace(
        get_settings=lambda pid: existing_settings,
        save_settings=lambda s: s,
    )
    service._publish_settings_updated = Mock()

    payload = AiProjectSettingsUpdate(
        enabled=True,
        preferred_provider="gemini",
        model_name="gemini-2.5-flash",
    )

    updated = service.update_settings(project_id, user_id, payload)
    assert updated.preferred_provider == "gemini"
    assert updated.model_name == "gemini-2.5-flash"
