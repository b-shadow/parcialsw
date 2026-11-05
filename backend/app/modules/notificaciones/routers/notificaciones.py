from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.notificaciones.schemas import (
    ActualizacionPreferenciasNotificacion,
    ElementoPreferenciaNotificacion,
    RespuestaCantidadNoLeidas,
    RespuestaNotificacion,
    RespuestaPaginaNotificaciones,
)
from app.modules.notificaciones.services import ServicioNotificaciones

router = APIRouter(prefix="/notifications", tags=["notificaciones"])


@router.get("", response_model=RespuestaPaginaNotificaciones)
def listar_notificaciones(
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    cursor: UUID | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    unread_only: bool = False,
) -> dict:
    items, has_more = ServicioNotificaciones(db).listar_por_usuario(
        current_user.id, cursor=cursor, limit=limit, unread_only=unread_only
    )
    return {
        "items": items,
        "next_cursor": str(items[-1].id) if has_more and items else None,
        "has_more": has_more,
    }


@router.get("/unread-count", response_model=RespuestaCantidadNoLeidas)
def cantidad_no_leidas(
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> dict[str, int]:
    return {"count": ServicioNotificaciones(db).cantidad_no_leidas(current_user.id)}


def _marcar(notification_id: UUID, user_id: UUID, db: Session, *, clicked: bool) -> RespuestaNotificacion:
    try:
        return ServicioNotificaciones(db).marcar_leida(notification_id, user_id, clicked=clicked)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notificacion no encontrada"},
        ) from exc


@router.post("/{notification_id}/read", response_model=RespuestaNotificacion)
def marcar_leida(
    notification_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaNotificacion:
    return _marcar(notification_id, current_user.id, db, clicked=False)


@router.post("/{notification_id}/clicked", response_model=RespuestaNotificacion)
def marcar_abierta(
    notification_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaNotificacion:
    return _marcar(notification_id, current_user.id, db, clicked=True)


@router.post("/read-all")
def marcar_todas_leidas(
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    before: datetime | None = None,
) -> dict[str, int]:
    return {"updated": ServicioNotificaciones(db).marcar_todas_leidas(current_user.id, before=before)}


@router.get("/preferences", response_model=list[ElementoPreferenciaNotificacion])
def preferences(
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list:
    return ServicioNotificaciones(db).preferences(current_user.id)


@router.put("/preferences", response_model=list[ElementoPreferenciaNotificacion])
def actualizar_preferencias(
    payload: ActualizacionPreferenciasNotificacion,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list:
    return ServicioNotificaciones(db).reemplazar_preferencias(
        current_user.id, [item.model_dump() for item in payload.items]
    )
