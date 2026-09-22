from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.password import hash_password, verify_password
from app.modules.acceso_usuarios.models import User, UserRole
from app.modules.acceso_usuarios.repositories.role_repository import RoleRepository
from app.modules.acceso_usuarios.repositories.user_repository import UserRepository
from app.modules.acceso_usuarios.schemas.user import AdminUserUpdateRequest, ChangePasswordRequest
from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.acceso_usuarios.validators.user_validator import ensure_user_exists


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.audit = AuditService(db)

    def list_users(self) -> list[User]:
        return self.users.list()

    def update_user(self, user_id: UUID, payload: AdminUserUpdateRequest, actor_id: UUID) -> User:
        user = ensure_user_exists(self.users.get_by_id(user_id))
        data = payload.model_dump(exclude_unset=True, exclude={"role_name"})
        for field, value in data.items():
            setattr(user, field, value)
        if payload.role_name is not None:
            role = self.roles.get_by_name(payload.role_name)
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rol global no valido",
                )
            user.roles.clear()
            user.roles.append(UserRole(user_id=user.id, role_id=role.id))
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

    def change_password(self, user_id: UUID, payload: ChangePasswordRequest) -> None:
        user = ensure_user_exists(self.users.get_by_id(user_id))
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
