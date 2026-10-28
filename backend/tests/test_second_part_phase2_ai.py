from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from ai_engine.providers.base import ProviderHealth
from ai_engine.providers.ollama_provider import validate_ollama_base_url
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import UniqueConstraint

from app.main import app
from app.modules.asistente_proyecto.models import AiConversation
from app.modules.asistente_proyecto.schemas.assistant import (
    AiConversationCreate,
    AiInteractionRequest,
    AiProviderHealthResponse,
)
from app.modules.asistente_proyecto.services.assistant_service import AssistantContractService
from app.modules.asistente_proyecto.services.project_ai_application_service import (
    ProjectAiApplicationService,
)
from app.modules.asistente_proyecto.services.provider_factory import resolve_ollama_model


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
    request = AiInteractionRequest(client_message_id=uuid4(), content="  revisa el modelo  ")
    assert request.content == "revisa el modelo"
    with pytest.raises(ValidationError):
        AiInteractionRequest(client_message_id=uuid4(), content="revisa", base_diagram_version=-1)


def test_project_can_store_multiple_named_conversations() -> None:
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in AiConversation.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("project_id",) not in unique_columns
    assert AiConversationCreate(title="  Revision de dominio  ").title == "Revision de dominio"
    assert (
        AssistantContractService._title_from_first_message(
            "Analiza el diagrama de ventas y recomienda mejoras importantes"
        )
        == "Analiza el diagrama de ventas y recomienda mejoras"
    )


def test_provider_health_contract_does_not_expose_internal_data() -> None:
    response = AiProviderHealthResponse(
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
    }


def test_ollama_configuration_rejects_ssrf_destinations() -> None:
    assert validate_ollama_base_url("http://localhost:11434")
    with pytest.raises(ValueError):
        validate_ollama_base_url("http://169.254.169.254/latest/meta-data")


def test_missing_configured_model_uses_an_installed_local_qwen_model() -> None:
    class FakeProvider:
        async def health(self, requested_model: str) -> ProviderHealth:
            return ProviderHealth(
                provider="ollama",
                available=True,
                installed_models=["qwen3-vl:2b-instruct"],
                requested_model=requested_model,
                requested_model_available=False,
            )

    import asyncio

    selected = asyncio.run(resolve_ollama_model(FakeProvider(), "qwen2.5-coder:7b"))
    assert selected == "qwen3-vl:2b-instruct"


def test_assistant_resolves_the_only_diagram_from_the_project() -> None:
    project_id = uuid4()
    diagram_id = uuid4()
    service = ProjectAiApplicationService(Mock())
    service.uml = SimpleNamespace(
        list_diagrams_by_project=lambda _: [SimpleNamespace(id=diagram_id)]
    )

    assert service._resolve_project_diagram_id(project_id, None) == diagram_id


def test_assistant_rejects_a_diagram_from_another_project() -> None:
    project_id = uuid4()
    own_diagram_id = uuid4()
    service = ProjectAiApplicationService(Mock())
    service.uml = SimpleNamespace(
        list_diagrams_by_project=lambda _: [SimpleNamespace(id=own_diagram_id)]
    )

    with pytest.raises(HTTPException) as error:
        service._resolve_project_diagram_id(project_id, uuid4())

    assert error.value.status_code == 404
    assert error.value.detail["code"] == "PROJECT_DIAGRAM_NOT_FOUND"
