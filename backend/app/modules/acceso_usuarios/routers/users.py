from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user, require_admin
from app.modules.acceso_usuarios.models import AuditLog, Role, User
from app.modules.acceso_usuarios.schemas.user import (
    AdminUserUpdateRequest,
    AuditLogResponse,
    ChangePasswordRequest,
    RoleResponse,
    UserResponse,
)
from app.modules.acceso_usuarios.repositories.role_repository import RoleRepository
from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.acceso_usuarios.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["usuarios"])


@router.get("", response_model=list[UserResponse])
def list_users(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[User]:
    return UserService(db).list_users()


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Role]:
    return RoleRepository(db).list()


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    module: str | None = None,
    action: str | None = None,
    user_id: UUID | None = None,
    project_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AuditLog]:
    return AuditService(db).list_logs(
        module=module,
        action=action,
        user_id=user_id,
        project_id=project_id,
        limit=limit,
    )


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    UserService(db).change_password(current_user.id, payload)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    payload: AdminUserUpdateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    return UserService(db).update_user(user_id, payload, current_user.id)
