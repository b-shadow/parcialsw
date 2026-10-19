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
    revision: int = 0

    model_config = {"from_attributes": True}


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    project_role: str
    joined_at: datetime | None
    full_name: str | None = None
    email: str | None = None

    model_config = {"from_attributes": True}


class ProjectMemberCandidateResponse(BaseModel):
    id: UUID
    full_name: str
    email: str


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
    expected_project_revision: int | None = Field(default=None, ge=0)
    allow_duplicate: bool = False


class VersionResponse(BaseModel):
    id: UUID
    project_id: UUID
    created_by_user_id: UUID
    version_number: int
    name: str
    description: str | None
    status: str
    created_at: datetime
    created_by_name: str | None = None
    kind: str = "manual"
    snapshot_schema_version: int = 2
    snapshot_hash: str = ""
    snapshot_size_bytes: int = 0
    project_revision: int = 0

    model_config = {"from_attributes": True}


class VersionRestoreResponse(BaseModel):
    restored_version: VersionResponse
    backup_version: VersionResponse
    restored_diagram_ids: list[UUID]
    restore_operation_id: UUID
    project_revision: int
    idempotent_replay: bool = False


class RestoreRequest(BaseModel):
    expected_project_revision: int | None = Field(default=None, ge=0)


class RestorePreviewResponse(BaseModel):
    version: VersionResponse
    current_revision: int
    effective_schema_version: int
    summary: dict
    differences: dict
    warnings: list[str] = Field(default_factory=list)


class ActivityPageResponse(BaseModel):
    items: list["CollaborationEventResponse"]
    next_cursor: int | None
    has_more: bool
    latest_sequence: int


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
    resource_type: str | None = None
    resource_id: UUID | None = None
    correlation_id: UUID | None = None
    causation_id: UUID | None = None
    summary_key: str | None = None
