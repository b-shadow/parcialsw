from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.notificaciones.schemas import (
    PushConfigResponse,
    PushSubscriptionCreate,
    PushSubscriptionDelete,
    PushSubscriptionResponse,
)
from app.modules.notificaciones.services import PushNotificationService, send_user_push

router = APIRouter(prefix="/notifications/push", tags=["notificaciones-push"])


@router.get("/config", response_model=PushConfigResponse)
def push_config(_: Annotated[User, Depends(get_current_user)]) -> PushConfigResponse:
    enabled = bool(settings.vapid_public_key and settings.vapid_private_key)
    return PushConfigResponse(
        enabled=enabled,
        public_key=settings.vapid_public_key if enabled else None,
    )


@router.post("/subscriptions", response_model=PushSubscriptionResponse, status_code=201)
def subscribe(
    payload: PushSubscriptionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    user_agent: Annotated[str | None, Header()] = None,
) -> PushSubscriptionResponse:
    return PushNotificationService(db).subscribe(
        current_user.id,
        payload,
        user_agent,
    )


@router.delete("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(
    payload: PushSubscriptionDelete,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    PushNotificationService(db).unsubscribe(current_user.id, str(payload.endpoint))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/test", status_code=status.HTTP_202_ACCEPTED)
def test_notification(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    background_tasks.add_task(
        send_user_push,
        current_user.id,
        {
            "title": "Notificaciones activadas",
            "body": "CASE Inteligente puede avisarte sobre proyectos, versiones y generaciones.",
            "url": "/perfil",
            "tag": "push-test",
        },
    )
    return {"status": "queued"}
