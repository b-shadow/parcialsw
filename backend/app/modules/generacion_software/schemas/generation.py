from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TransformationRequest(BaseModel):
    diagram_id: UUID
    target_platform: str = Field(pattern="^(spring_boot|flutter|full_stack)$")
    source_version: str | None = None


class TransformationResponse(BaseModel):
    id: UUID
    project_id: UUID
    diagram_id: UUID
    requested_by_user_id: UUID
    source_version: str | None
    target_platform: str
    intermediate_model: dict
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BackendGenerationRequest(BaseModel):
    transformation_id: UUID
    name: str = Field(min_length=2, max_length=160)
    version_label: str = "v1"


class FrontendGenerationRequest(BaseModel):
    transformation_id: UUID
    name: str = Field(min_length=2, max_length=160)
    version_label: str = "v1"
    backend_id: UUID | None = None
    api_base_url: str | None = Field(default=None, max_length=255)


class GeneratedBackendResponse(BaseModel):
    id: UUID
    project_id: UUID
    transformation_id: UUID
    generated_by_user_id: UUID
    name: str
    technology: str
    language: str
    database_engine: str
    version_label: str
    status: str
    artifact_path: str | None
    manifest: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class GeneratedFrontendResponse(BaseModel):
    id: UUID
    project_id: UUID
    transformation_id: UUID
    generated_by_user_id: UUID
    backend_id: UUID | None
    name: str
    technology: str
    language: str
    version_label: str
    status: str
    artifact_path: str | None
    manifest: dict
    created_at: datetime

    model_config = {"from_attributes": True}
