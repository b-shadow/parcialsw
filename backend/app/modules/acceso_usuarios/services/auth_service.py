from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.jwt import create_access_token
from app.core.security.password import hash_password, verify_password
from app.modules.acceso_usuarios.models import User, UserRole
from app.modules.acceso_usuarios.repositories.role_repository import RoleRepository
from app.modules.acceso_usuarios.repositories.user_repository import UserRepository
from app.modules.acceso_usuarios.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.acceso_usuarios.validators.user_validator import ensure_email_available


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.audit = AuditService(db)

    def register(self, payload: RegisterRequest) -> User:
        email = payload.email.lower()
        ensure_email_available(self.users.get_by_email(email))
        user = User(
            full_name=payload.full_name.strip(),
            email=email,
            password_hash=hash_password(payload.password),
            is_active=True,
        )
        self.users.add(user)

        editor_role = self.roles.get_by_name("EDITOR")
        if editor_role is not None:
            self.db.add(UserRole(user_id=user.id, role_id=editor_role.id))

        self.audit.record(module="acceso_usuarios", action="REGISTER_USER", user_id=user.id)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(payload.email.lower())
        if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales invalidas",
            )
        user.last_access_at = datetime.now(UTC)
        self.audit.record(module="acceso_usuarios", action="LOGIN", user_id=user.id)
        self.db.commit()
        return TokenResponse(access_token=create_access_token(user.id))

