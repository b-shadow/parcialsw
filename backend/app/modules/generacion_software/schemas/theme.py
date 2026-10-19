from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.generacion_software.schemas.theme_contract import (
    FlutterThemeConfigV2,
    ThemeDiagnostic,
)


class FlutterThemeUpdate(BaseModel):
    config: dict
    preset_name: str | None = Field(default=None, max_length=120)


class FlutterThemeMutation(BaseModel):
    expected_revision: int | None = Field(default=None, ge=1)


class FlutterThemeValidationRequest(BaseModel):
    config: dict


class FlutterThemeValidationResponse(BaseModel):
    theme: FlutterThemeConfigV2
    diagnostics: list[ThemeDiagnostic]
    normalized_fields: list[str]
    valid: bool


class FlutterThemeResponse(FlutterThemeValidationResponse):
    id: UUID | None
    project_id: UUID
    preset_name: str | None
    schema_version: Literal[2] = 2
    revision: int
    created_by_user_id: UUID | None
    updated_by_user_id: UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class FlutterThemePresetWrite(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    config: dict


class FlutterThemePresetResponse(BaseModel):
    id: str
    kind: Literal["system", "custom"]
    name: str
    description: str | None = None
    config: FlutterThemeConfigV2
    schema_version: Literal[2] = 2
    updated_at: datetime | None = None


class FlutterThemePresetApply(BaseModel):
    expected_revision: int = Field(ge=1)
