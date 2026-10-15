from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    settings: dict = Field(default_factory=dict)


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = None
    status: str | None = Field(default=None, max_length=40)
    settings: dict | None = None


class ProjectResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    status: str
    settings: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    project_role: str
    joined_at: datetime | None

    model_config = {"from_attributes": True}


class AddMemberRequest(BaseModel):
    user_id: UUID
    project_role: str = Field(pattern="^(ORGANIZADOR|EDITOR)$")


class UpdateMemberRequest(BaseModel):
    project_role: str = Field(pattern="^(ORGANIZADOR|EDITOR)$")


class PermissionRequest(BaseModel):
    permission_code: str = Field(min_length=2, max_length=80)
    is_allowed: bool = True


class VersionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    snapshot: dict = Field(default_factory=dict)


class VersionResponse(BaseModel):
    id: UUID
    project_id: UUID
    created_by_user_id: UUID
    version_number: int
    name: str
    description: str | None
    snapshot: dict
    status: str
    created_at: datetime
    created_by_name: str | None = None

    model_config = {"from_attributes": True}


class VersionRestoreResponse(BaseModel):
    restored_version: VersionResponse
    backup_version: VersionResponse
    restored_diagram_ids: list[UUID]


class CollaborationEventResponse(BaseModel):
    id: UUID
    project_id: UUID
    diagram_id: UUID | None
    user_id: UUID
    user_name: str
    client_event_id: UUID
    sequence_number: int
    event_type: str
    element_type: str | None
    element_id: UUID | None
    base_version: int | None
    payload: dict
    created_at: datetime
