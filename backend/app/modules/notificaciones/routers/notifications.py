from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.notificaciones.schemas import (
    NotificationPageResponse,
    NotificationPreferenceItem,
    NotificationPreferencesUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.modules.notificaciones.services import NotificationService

router = APIRouter(prefix="/notifications", tags=["notificaciones"])


@router.get("", response_model=NotificationPageResponse)
def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    cursor: UUID | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    unread_only: bool = False,
) -> dict:
    items, has_more = NotificationService(db).list_for_user(
        current_user.id, cursor=cursor, limit=limit, unread_only=unread_only
    )
    return {
        "items": items,
        "next_cursor": str(items[-1].id) if has_more and items else None,
        "has_more": has_more,
    }


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, int]:
    return {"count": NotificationService(db).unread_count(current_user.id)}


def _mark(notification_id: UUID, user_id: UUID, db: Session, *, clicked: bool) -> NotificationResponse:
    try:
        return NotificationService(db).mark_read(notification_id, user_id, clicked=clicked)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notificacion no encontrada"},
        ) from exc


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationResponse:
    return _mark(notification_id, current_user.id, db, clicked=False)


@router.post("/{notification_id}/clicked", response_model=NotificationResponse)
def mark_clicked(
    notification_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationResponse:
    return _mark(notification_id, current_user.id, db, clicked=True)


@router.post("/read-all")
def mark_all_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    before: datetime | None = None,
) -> dict[str, int]:
    return {"updated": NotificationService(db).mark_all_read(current_user.id, before=before)}


@router.get("/preferences", response_model=list[NotificationPreferenceItem])
def preferences(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list:
    return NotificationService(db).preferences(current_user.id)


@router.put("/preferences", response_model=list[NotificationPreferenceItem])
def update_preferences(
    payload: NotificationPreferencesUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list:
    return NotificationService(db).replace_preferences(
        current_user.id, [item.model_dump() for item in payload.items]
    )
