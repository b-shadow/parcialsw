from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.notificaciones.schemas import (
    CreacionSuscripcionPush,
    EliminacionSuscripcionPush,
    RegistroDispositivoMovil,
    RespuestaConfiguracionPush,
    RespuestaSuscripcionPush,
)
from app.modules.notificaciones.services import ServicioNotificacionesPush, enviar_push_usuario

router = APIRouter(prefix="/notifications/push", tags=["notificaciones-push"])


@router.get("/config", response_model=RespuestaConfiguracionPush)
def configuracion_push(_: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> RespuestaConfiguracionPush:
    enabled = bool(settings.vapid_public_key and settings.vapid_private_key)
    return RespuestaConfiguracionPush(
        enabled=enabled,
        public_key=settings.vapid_public_key if enabled else None,
    )


@router.post("/subscriptions", response_model=RespuestaSuscripcionPush, status_code=201)
def suscribir(
    payload: CreacionSuscripcionPush,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    user_agent: Annotated[str | None, Header()] = None,
) -> RespuestaSuscripcionPush:
    return ServicioNotificacionesPush(db).suscribir(
        current_user.id,
        payload,
        user_agent,
    )


@router.post("/mobile-device", status_code=status.HTTP_201_CREATED)
def registrar_dispositivo_movil(
    payload: RegistroDispositivoMovil,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> dict[str, str]:
    ServicioNotificacionesPush(db).suscribir_dispositivo_movil(
        current_user.id,
        payload.endpoint,
    )
    return {"status": "ok"}


@router.delete("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_suscripcion(
    payload: EliminacionSuscripcionPush,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> Response:
    ServicioNotificacionesPush(db).cancelar_suscripcion(current_user.id, str(payload.endpoint))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/test", status_code=status.HTTP_202_ACCEPTED)
def probar_notificacion(
    background_tasks: BackgroundTasks,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
) -> dict[str, str]:
    background_tasks.add_task(
        enviar_push_usuario,
        current_user.id,
        {
            "title": "Notificaciones activadas",
            "body": "CASE Inteligente puede avisarte sobre proyectos, versiones y generaciones.",
            "url": "/perfil",
            "tag": "push-test",
        },
    )
    return {"status": "queued"}
