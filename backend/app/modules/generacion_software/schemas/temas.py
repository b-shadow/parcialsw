from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.generacion_software.schemas.contrato_temas import (
    ConfiguracionTemaFlutterV2,
    DiagnosticoTema,
)


class ActualizacionTemaFlutter(BaseModel):
    config: dict
    preset_name: str | None = Field(default=None, max_length=120)


class MutacionTemaFlutter(BaseModel):
    expected_revision: int | None = Field(default=None, ge=1)


class SolicitudValidacionTemaFlutter(BaseModel):
    config: dict


class RespuestaValidacionTemaFlutter(BaseModel):
    theme: ConfiguracionTemaFlutterV2
    diagnostics: list[DiagnosticoTema]
    normalized_fields: list[str]
    valid: bool


class RespuestaTemaFlutter(RespuestaValidacionTemaFlutter):
    id: UUID | None
    project_id: UUID
    preset_name: str | None
    schema_version: Literal[2] = 2
    revision: int
    created_by_user_id: UUID | None
    updated_by_user_id: UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class EscrituraTemaFlutterPredefinido(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    config: dict


class RespuestaTemaFlutterPredefinido(BaseModel):
    id: str
    kind: Literal["system", "custom"]
    name: str
    description: str | None = None
    config: ConfiguracionTemaFlutterV2
    schema_version: Literal[2] = 2
    updated_at: datetime | None = None


class AplicacionTemaFlutterPredefinido(BaseModel):
    expected_revision: int = Field(ge=1)
