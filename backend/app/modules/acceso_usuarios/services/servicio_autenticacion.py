from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.contrasena import hash_password, verify_password
from app.core.security.jwt import crear_token_acceso
from app.modules.acceso_usuarios.models import RolUsuario, Usuario
from app.modules.acceso_usuarios.repositories.repositorio_roles import RepositorioRoles
from app.modules.acceso_usuarios.repositories.repositorio_usuarios import RepositorioUsuarios
from app.modules.acceso_usuarios.schemas.autenticacion import (
    RespuestaToken,
    SolicitudIngreso,
    SolicitudRegistro,
)
from app.modules.acceso_usuarios.services.servicio_auditoria import ServicioAuditoria
from app.modules.acceso_usuarios.validators.validador_usuario import asegurar_correo_disponible


class ServicioAutenticacion:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = RepositorioUsuarios(db)
        self.roles = RepositorioRoles(db)
        self.audit = ServicioAuditoria(db)

    def registrar(self, payload: SolicitudRegistro) -> Usuario:
        email = payload.email.lower()
        asegurar_correo_disponible(self.users.obtener_por_correo(email))
        user = Usuario(
            full_name=payload.full_name.strip(),
            email=email,
            password_hash=hash_password(payload.password),
            is_active=True,
        )
        self.users.add(user)

        editor_role = self.roles.obtener_por_nombre("EDITOR")
        if editor_role is not None:
            self.db.add(RolUsuario(user_id=user.id, role_id=editor_role.id))

        self.audit.record(module="acceso_usuarios", action="REGISTER_USER", user_id=user.id)
        self.db.commit()
        self.db.refresh(user)
        return user

    def ingresar(self, payload: SolicitudIngreso) -> RespuestaToken:
        user = self.users.obtener_por_correo(payload.email.lower())
        if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales invalidas",
            )
        user.last_access_at = datetime.now(UTC)
        self.audit.record(module="acceso_usuarios", action="LOGIN", user_id=user.id)
        self.db.commit()
        return RespuestaToken(access_token=crear_token_acceso(user.id))
