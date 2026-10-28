from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.asistente_proyecto.schemas import (
    AiActionDecisionResponse,
    AiActionResponse,
    AiConversationCreate,
    AiConversationResponse,
    AiConversationUpdate,
    AiInteractionRequest,
    AiInteractionResponse,
    AiMessagePage,
    AiProjectSettingsResponse,
    AiProjectSettingsUpdate,
    AiProviderHealthResponse,
    AiRecommendationResponse,
    AiRecommendationStatusUpdate,
)
from app.modules.asistente_proyecto.services import (
    AiActionExecutionService,
    AssistantContractService,
    ProjectAiApplicationService,
)
from app.modules.asistente_proyecto.services.conversation_memory_service import (
    summarize_project_conversation,
)
from app.modules.asistente_proyecto.services.event_publisher import ProjectAiEventPublisher

router = APIRouter(prefix="/projects", tags=["asistente-proyecto"])


@router.post("/{project_id}/ai/interactions", response_model=AiInteractionResponse)
async def create_ai_interaction(
    project_id: UUID,
    payload: AiInteractionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    response = await ProjectAiApplicationService(db).interact(project_id, current_user.id, payload)
    background_tasks.add_task(
        summarize_project_conversation, project_id, current_user.id, payload.conversation_id
    )
    return response


@router.get("/{project_id}/ai/provider-health", response_model=AiProviderHealthResponse)
async def get_ai_provider_health(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return await ProjectAiApplicationService(db).provider_health(project_id, current_user.id)


@router.post(
    "/{project_id}/ai/actions/{action_id}/confirm",
    response_model=AiActionDecisionResponse,
)
async def confirm_ai_action(
    project_id: UUID,
    action_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    action, idempotent = AiActionExecutionService(db).confirm(
        project_id, action_id, current_user.id
    )
    if not idempotent:
        await ProjectAiEventPublisher().publish_persisted(
            project_id=project_id,
            actor_user_id=current_user.id,
            event_type="AI_ACTION_STATUS_CHANGED",
            payload=AiActionResponse.model_validate(action).model_dump(mode="json"),
            correlation_id=uuid4(),
            conversation_sequence=None,
        )
        if action.action_type == "update_method_specification":
            plan = action.payload.get("_plan") or {}
            result = action.result_json or {}
            await ProjectAiEventPublisher().publish_persisted(
                project_id=project_id,
                actor_user_id=current_user.id,
                event_type=(
                    "METHOD_SPECIFICATION_CREATED"
                    if result.get("created")
                    else "METHOD_SPECIFICATION_UPDATED"
                ),
                payload={
                    "diagram_id": plan.get("diagram_id"),
                    "method_id": result.get("method_id") or str(action.target_id),
                    "class_id": result.get("class_id"),
                    "revision": result.get("revision"),
                    "changed_fields": [key for key in action.payload if key != "_plan"],
                },
                correlation_id=uuid4(),
                diagram_id=UUID(plan["diagram_id"]) if plan.get("diagram_id") else None,
                conversation_sequence=None,
            )
    return AiActionDecisionResponse(action=action, idempotent=idempotent)


@router.post(
    "/{project_id}/ai/actions/{action_id}/reject",
    response_model=AiActionDecisionResponse,
)
async def reject_ai_action(
    project_id: UUID,
    action_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    action, idempotent = AiActionExecutionService(db).reject(project_id, action_id, current_user.id)
    if not idempotent:
        await ProjectAiEventPublisher().publish_persisted(
            project_id=project_id,
            actor_user_id=current_user.id,
            event_type="AI_ACTION_STATUS_CHANGED",
            payload=AiActionResponse.model_validate(action).model_dump(mode="json"),
            correlation_id=uuid4(),
            conversation_sequence=None,
        )
    return AiActionDecisionResponse(action=action, idempotent=idempotent)


@router.get("/{project_id}/ai/settings", response_model=AiProjectSettingsResponse)
def get_ai_settings(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return AssistantContractService(db).get_settings(project_id, current_user.id)


@router.put("/{project_id}/ai/settings", response_model=AiProjectSettingsResponse)
def update_ai_settings(
    project_id: UUID,
    payload: AiProjectSettingsUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return AssistantContractService(db).update_settings(project_id, current_user.id, payload)


@router.get("/{project_id}/ai/conversation", response_model=AiConversationResponse)
def get_ai_conversation(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return AssistantContractService(db).get_conversation(project_id, current_user.id)


@router.get(
    "/{project_id}/ai/conversations",
    response_model=list[AiConversationResponse],
)
def list_ai_conversations(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    service = AssistantContractService(db)
    conversations = service.list_conversations(project_id, current_user.id)
    return conversations or [service.get_conversation(project_id, current_user.id)]


@router.post(
    "/{project_id}/ai/conversations",
    response_model=AiConversationResponse,
    status_code=201,
)
def create_ai_conversation(
    project_id: UUID,
    payload: AiConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return AssistantContractService(db).create_conversation(project_id, current_user.id, payload)


@router.patch(
    "/{project_id}/ai/conversations/{conversation_id}",
    response_model=AiConversationResponse,
)
def update_ai_conversation(
    project_id: UUID,
    conversation_id: UUID,
    payload: AiConversationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return AssistantContractService(db).update_conversation(
        project_id, conversation_id, current_user.id, payload
    )


@router.get("/{project_id}/ai/messages", response_model=AiMessagePage)
async def list_ai_messages(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    before_sequence: int | None = Query(default=None, ge=1),
    after_sequence: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    conversation_id: Annotated[UUID | None, Query()] = None,
):
    return await AssistantContractService(db).list_messages(
        project_id,
        current_user.id,
        before_sequence,
        after_sequence,
        limit,
        conversation_id,
    )


@router.get("/{project_id}/ai/actions", response_model=list[AiActionResponse])
def list_ai_actions(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    action_status: str | None = Query(default=None, alias="status", max_length=30),
    limit: int = Query(default=50, ge=1, le=200),
    conversation_id: Annotated[UUID | None, Query()] = None,
):
    return AssistantContractService(db).list_actions(
        project_id, current_user.id, action_status, limit, conversation_id
    )


@router.get("/{project_id}/ai/actions/{action_id}", response_model=AiActionResponse)
def get_ai_action(
    project_id: UUID,
    action_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return AssistantContractService(db).get_action(project_id, action_id, current_user.id)


@router.get("/{project_id}/ai/recommendations", response_model=list[AiRecommendationResponse])
def list_ai_recommendations(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    item_status: str | None = Query(default=None, alias="status", max_length=30),
    severity: str | None = Query(default=None, max_length=20),
    limit: int = Query(default=50, ge=1, le=200),
    conversation_id: Annotated[UUID | None, Query()] = None,
):
    return AssistantContractService(db).list_recommendations(
        project_id, current_user.id, item_status, severity, limit, conversation_id
    )


@router.patch(
    "/{project_id}/ai/recommendations/{recommendation_id}",
    response_model=AiRecommendationResponse,
)
async def update_ai_recommendation(
    project_id: UUID,
    recommendation_id: UUID,
    payload: AiRecommendationStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    recommendation = AssistantContractService(db).update_recommendation(
        project_id, recommendation_id, current_user.id, payload
    )
    await ProjectAiEventPublisher().publish_persisted(
        project_id=project_id,
        actor_user_id=current_user.id,
        event_type="AI_RECOMMENDATION_STATUS_CHANGED",
        payload=AiRecommendationResponse.model_validate(recommendation).model_dump(mode="json"),
        correlation_id=uuid4(),
        conversation_sequence=None,
    )
    return recommendation
