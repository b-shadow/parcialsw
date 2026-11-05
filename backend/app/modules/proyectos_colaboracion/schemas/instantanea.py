import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.generacion_software.schemas.contrato_temas import ConfiguracionTemaFlutterV2

SENSITIVE_KEY_PARTS = (
    "api_key",
    "authorization",
    "database_url",
    "password",
    "private_key",
    "secret",
    "token",
)


def sanear_configuracion_instantanea(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: sanear_configuracion_instantanea(child)
            for key, child in value.items()
            if not any(part in str(key).casefold() for part in SENSITIVE_KEY_PARTS)
        }
    if isinstance(value, list):
        return [sanear_configuracion_instantanea(child) for child in value]
    return value


class InstantaneaProyecto(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None


class InstantaneaConfiguracionIA(BaseModel):
    enabled: bool = True
    preferred_provider: Literal["ollama", "gemini", "rule_engine"] = "ollama"
    model_name: str = Field(default="qwen2.5:7b", min_length=1, max_length=120)
    fallback_enabled: bool = True
    require_confirmation: bool = True


class InstantaneaTemaFlutter(BaseModel):
    config: ConfiguracionTemaFlutterV2
    preset_name: str | None = Field(default=None, max_length=120)
    schema_version: int = Field(default=2, ge=2)
    revision: int = Field(default=1, ge=1)


class InstantaneaProyectoV2(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[2] = 2
    captured_at: datetime
    project: InstantaneaProyecto
    diagrams: list[dict[str, Any]] = Field(default_factory=list)
    flutter_theme: InstantaneaTemaFlutter | None = None
    generation_settings: dict[str, Any] = Field(default_factory=dict)
    ai_settings: InstantaneaConfiguracionIA | None = None

    @field_validator("captured_at")
    @classmethod
    def requerir_zona_horaria(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("captured_at debe incluir zona horaria")
        return value.astimezone(UTC)

    @field_validator("generation_settings", mode="before")
    @classmethod
    def eliminar_configuracion_generacion_sensible(cls, value: object) -> object:
        return sanear_configuracion_instantanea(value)


def adaptar_instantanea_v1(snapshot: dict, project: InstantaneaProyecto) -> InstantaneaProyectoV2:
    version = snapshot.get("schema_version", 1)
    if version != 1:
        raise ValueError(f"Version de snapshot no soportada: {version}")
    return InstantaneaProyectoV2(
        captured_at=datetime.now(UTC),
        project=project,
        diagrams=snapshot.get("diagrams", []),
    )


def actualizar_instantanea_v1_a_v2(
    snapshot: dict,
    project: InstantaneaProyecto,
    *,
    generation_settings: dict[str, Any] | None = None,
    flutter_theme: InstantaneaTemaFlutter | None = None,
    ai_settings: InstantaneaConfiguracionIA | None = None,
) -> tuple[InstantaneaProyectoV2, list[str]]:
    """Upgrade a legacy snapshot in memory without mutating its stored representation."""
    upgraded = adaptar_instantanea_v1(snapshot, project)
    upgraded.generation_settings = generation_settings or {}
    upgraded.flutter_theme = flutter_theme
    upgraded.ai_settings = ai_settings
    return upgraded, [
        "snapshot_v1_adapted",
        "missing_settings_completed_from_current_defaults",
    ]


def analizar_instantanea_proyecto(snapshot: dict, project: InstantaneaProyecto) -> InstantaneaProyectoV2:
    version = snapshot.get("schema_version", 1)
    if version == 1:
        return adaptar_instantanea_v1(snapshot, project)
    if version == 2:
        parsed = InstantaneaProyectoV2.model_validate(snapshot)
        if parsed.project.id != project.id:
            raise ValueError("El snapshot pertenece a otro proyecto")
        return parsed
    raise ValueError(f"Version de snapshot no soportada: {version}")


def normalizar_instantanea_proyecto(snapshot: InstantaneaProyectoV2 | dict) -> bytes:
    parsed = snapshot if isinstance(snapshot, InstantaneaProyectoV2) else InstantaneaProyectoV2.model_validate(snapshot)
    value = parsed.model_dump(mode="json", exclude={"captured_at"})
    if value.get("flutter_theme"):
        value["flutter_theme"].pop("revision", None)
    value["diagrams"] = sorted(value.get("diagrams", []), key=lambda item: str(item.get("id", "")))
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def hash_instantanea_sha256(snapshot: InstantaneaProyectoV2 | dict) -> str:
    return hashlib.sha256(normalizar_instantanea_proyecto(snapshot)).hexdigest()

