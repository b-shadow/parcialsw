from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_system: bool

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    is_active: bool
    last_access_at: datetime | None
    created_at: datetime
    role_names: list[str] = []

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    is_active: bool | None = None


class AdminUserUpdateRequest(UserUpdateRequest):
    role_name: str | None = Field(default=None, pattern="^(ADMINISTRADOR|EDITOR|ORGANIZADOR)$")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    project_id: UUID | None
    module: str
    action: str
    result: str
    detail: str | None
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}
