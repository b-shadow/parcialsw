from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.acceso_usuarios.schemas.user import UserResponse, UserUpdateRequest
from app.modules.acceso_usuarios.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["usuarios"])


@router.get("", response_model=list[UserResponse])
def list_users(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[User]:
    return UserService(db).list_users()


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    return UserService(db).update_user(user_id, payload, current_user.id)

