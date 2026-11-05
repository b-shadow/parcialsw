from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.contrasena import hash_password, verify_password
from app.modules.acceso_usuarios.models import RolUsuario, Usuario
from app.modules.acceso_usuarios.repositories.repositorio_roles import RepositorioRoles
from app.modules.acceso_usuarios.repositories.repositorio_usuarios import RepositorioUsuarios
from app.modules.acceso_usuarios.schemas.usuario import (
    SolicitudActualizacionUsuarioAdmin,
    SolicitudCambioContrasena,
)
from app.modules.acceso_usuarios.services.servicio_auditoria import ServicioAuditoria
from app.modules.acceso_usuarios.validators.validador_usuario import asegurar_usuario_existente


class ServicioUsuarios:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = RepositorioUsuarios(db)
        self.roles = RepositorioRoles(db)
        self.audit = ServicioAuditoria(db)

    def listar_usuarios(self) -> list[Usuario]:
        return self.users.list()

    def actualizar_usuario(self, user_id: UUID, payload: SolicitudActualizacionUsuarioAdmin, actor_id: UUID) -> Usuario:
        user = asegurar_usuario_existente(self.users.obtener_por_id(user_id))
        data = payload.model_dump(exclude_unset=True, exclude={"role_name"})
        for field, value in data.items():
            setattr(user, field, value)
        if payload.role_name is not None:
            role = self.roles.obtener_por_nombre(payload.role_name)
            if role is None or role.name not in {"ADMINISTRADOR", "EDITOR"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rol global no valido",
                )
            if user.roles:
                assignment = user.roles[0]
                assignment.role_id = role.id
                assignment.role = role
                for duplicate in user.roles[1:]:
                    self.db.delete(duplicate)
                user.roles[:] = [assignment]
            else:
                user.roles.append(RolUsuario(user_id=user.id, role_id=role.id, role=role))
        self.audit.record(
            module="acceso_usuarios",
            action="UPDATE_USER",
            user_id=actor_id,
            metadata={
                "target_user_id": str(user_id),
                "role_name": payload.role_name,
                "is_active": payload.is_active,
            },
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def cambiar_contrasena(self, user_id: UUID, payload: SolicitudCambioContrasena) -> None:
        user = asegurar_usuario_existente(self.users.obtener_por_id(user_id))
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contrasena actual no es correcta",
            )
        user.password_hash = hash_password(payload.new_password)
        self.audit.record(
            module="acceso_usuarios",
            action="CHANGE_PASSWORD",
            user_id=user_id,
        )
        self.db.commit()
