from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual, require_admin
from app.modules.acceso_usuarios.models import RegistroAuditoria, Rol, Usuario
from app.modules.acceso_usuarios.repositories.repositorio_roles import RepositorioRoles
from app.modules.acceso_usuarios.schemas.usuario import (
    RespuestaRegistroAuditoria,
    RespuestaRol,
    RespuestaUsuario,
    SolicitudActualizacionUsuarioAdmin,
    SolicitudCambioContrasena,
)
from app.modules.acceso_usuarios.services.servicio_auditoria import ServicioAuditoria
from app.modules.acceso_usuarios.services.servicio_usuarios import ServicioUsuarios

router = APIRouter(prefix="/users", tags=["usuarios"])


@router.get("", response_model=list[RespuestaUsuario])
def listar_usuarios(
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[Usuario]:
    return ServicioUsuarios(db).listar_usuarios()


@router.get("/roles", response_model=list[RespuestaRol])
def listar_roles(
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[Rol]:
    return RepositorioRoles(db).list()


@router.get("/audit-logs", response_model=list[RespuestaRegistroAuditoria])
def listar_registros_auditoria(
    _: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    module: str | None = None,
    action: str | None = None,
    user_id: UUID | None = None,
    project_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[RegistroAuditoria]:
    return ServicioAuditoria(db).listar_registros(
        module=module,
        action=action,
        user_id=user_id,
        project_id=project_id,
        limit=limit,
    )


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_mi_contrasena(
    payload: SolicitudCambioContrasena,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> None:
    ServicioUsuarios(db).cambiar_contrasena(current_user.id, payload)


@router.patch("/{user_id}", response_model=RespuestaUsuario)
def actualizar_usuario(
    user_id: UUID,
    payload: SolicitudActualizacionUsuarioAdmin,
    current_user: Annotated[Usuario, Depends(require_admin)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> Usuario:
    return ServicioUsuarios(db).actualizar_usuario(user_id, payload, current_user.id)
