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


class FlutterThemeConfig(BaseModel):
    primary_color: str = Field(default="#0F766E", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(default="#14B8A6", pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str = Field(default="#F8FAFC", pattern=r"^#[0-9A-Fa-f]{6}$")
    surface_color: str = Field(default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    button_color: str = Field(default="#0F766E", pattern=r"^#[0-9A-Fa-f]{6}$")
    font_family: str = Field(default="Roboto", max_length=80)
    border_radius: int = Field(default=12, ge=0, le=32)
    button_style: str = Field(default="filled", pattern="^(filled|outline|tonal)$")
    density: str = Field(default="normal", pattern="^(compact|normal|comfortable)$")


class FrontendGenerationRequest(BaseModel):
    transformation_id: UUID
    name: str = Field(min_length=2, max_length=160)
    version_label: str = "v1"
    backend_id: UUID | None = None
    api_base_url: str | None = Field(default=None, max_length=255)
    theme_config: dict | None = None


class CoordinatedPreflightRequest(BaseModel):
    transformation_id: UUID
    name: str = Field(min_length=2, max_length=160)
    theme_config: dict | None = None


class CoordinatedGenerationRequest(CoordinatedPreflightRequest):
    client_request_id: str = Field(min_length=8, max_length=120)
    api_base_url: str = Field(default="http://localhost:8080", max_length=255)
    verify: bool = True
    allow_unverified: bool = False


class GenerationPlanResponse(BaseModel):
    schema_version: int
    canonical_hash: str
    ready: bool
    errors: list[dict]
    plan: dict
    ui_manifest: dict


class CoordinatedGenerationResponse(BaseModel):
    id: UUID
    project_id: UUID
    transformation_id: UUID
    requested_by_user_id: UUID
    client_request_id: str
    name: str
    status: str
    stage: str
    plan_hash: str | None
    diagnostics: list
    manifest: dict
    artifact_path: str | None
    error_detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


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
