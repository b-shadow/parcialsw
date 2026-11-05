"""Routers para gestión de invitaciones al proyecto (V2.3)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.proyectos_colaboracion.schemas.invitacion import (
    RespuestaInvitacion,
    SolicitudCreacionInvitacion,
)
from app.modules.proyectos_colaboracion.schemas.proyecto import RespuestaIntegranteProyecto
from app.modules.proyectos_colaboracion.services.servicio_invitaciones import (
    ServicioInvitaciones,
)

router = APIRouter(prefix="/projects", tags=["invitaciones"])
my_router = APIRouter(prefix="/invitations", tags=["invitaciones"])


# 1. Crear invitación (organizador)
@router.post(
    "/{project_id}/invitations",
    status_code=status.HTTP_201_CREATED,
    response_model=RespuestaInvitacion,
)
def crear_invitacion(
    project_id: UUID,
    payload: SolicitudCreacionInvitacion,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaInvitacion:
    service = ServicioInvitaciones(db)
    invitation = service.invitar(project_id, payload, current_user.id)
    return service.convertir_a_respuesta(invitation)


# 2. Listar invitaciones por proyecto y estado (organizador)
@router.get(
    "/{project_id}/invitations",
    response_model=list[RespuestaInvitacion],
)
def listar_invitaciones_proyecto(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    status: str | None = Query(default=None),
) -> list[RespuestaInvitacion]:
    service = ServicioInvitaciones(db)
    items = service.listar_para_proyecto(project_id, current_user.id, status=status)
    return [service.convertir_a_respuesta(item) for item in items]


# 3. Revocar invitación (organizador)
@router.delete(
    "/{project_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revocar_invitacion(
    project_id: UUID,
    invitation_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> None:
    service = ServicioInvitaciones(db)
    service.revocar(project_id, invitation_id, current_user.id)


# 4. Bandeja del invitado: mis invitaciones pendientes
@my_router.get("/me", response_model=list[RespuestaInvitacion])
def listar_mis_invitaciones(
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[RespuestaInvitacion]:
    service = ServicioInvitaciones(db)
    items = service.listar_mias(current_user)
    return [service.convertir_a_respuesta(item) for item in items]


# 5. Bandeja del invitado: aceptar invitación
@my_router.post(
    "/{invitation_id}/accept",
    response_model=RespuestaIntegranteProyecto,
)
def aceptar_invitacion(
    invitation_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaIntegranteProyecto:
    service = ServicioInvitaciones(db)
    member = service.aceptar(invitation_id, current_user)
    return RespuestaIntegranteProyecto(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        project_role=member.project_role,
        joined_at=member.joined_at,
        full_name=current_user.full_name,
        email=current_user.email,
    )


# 6. Bandeja del invitado: rechazar invitación
@my_router.post(
    "/{invitation_id}/reject",
    response_model=RespuestaInvitacion,
)
def rechazar_invitacion(
    invitation_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> RespuestaInvitacion:
    service = ServicioInvitaciones(db)
    invitation = service.reject(invitation_id, current_user)
    return service.convertir_a_respuesta(invitation)
