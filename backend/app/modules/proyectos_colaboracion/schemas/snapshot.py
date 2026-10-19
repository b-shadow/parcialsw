import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.generacion_software.schemas.theme_contract import FlutterThemeConfigV2

SENSITIVE_KEY_PARTS = (
    "api_key",
    "authorization",
    "database_url",
    "password",
    "private_key",
    "secret",
    "token",
)


def sanitize_snapshot_settings(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: sanitize_snapshot_settings(child)
            for key, child in value.items()
            if not any(part in str(key).casefold() for part in SENSITIVE_KEY_PARTS)
        }
    if isinstance(value, list):
        return [sanitize_snapshot_settings(child) for child in value]
    return value


class SnapshotProject(BaseModel):
    id: UUID
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None


class SnapshotAiSettings(BaseModel):
    enabled: bool = True
    preferred_provider: Literal["ollama", "rule_engine"] = "ollama"
    model_name: str = Field(default="qwen2.5:7b", min_length=1, max_length=120)
    fallback_enabled: bool = True
    require_confirmation: bool = True


class SnapshotFlutterTheme(BaseModel):
    config: FlutterThemeConfigV2
    preset_name: str | None = Field(default=None, max_length=120)
    schema_version: int = Field(default=2, ge=2)
    revision: int = Field(default=1, ge=1)


class ProjectSnapshotV2(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[2] = 2
    captured_at: datetime
    project: SnapshotProject
    diagrams: list[dict[str, Any]] = Field(default_factory=list)
    flutter_theme: SnapshotFlutterTheme | None = None
    generation_settings: dict[str, Any] = Field(default_factory=dict)
    ai_settings: SnapshotAiSettings | None = None

    @field_validator("captured_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("captured_at debe incluir zona horaria")
        return value.astimezone(UTC)

    @field_validator("generation_settings", mode="before")
    @classmethod
    def remove_sensitive_generation_settings(cls, value: object) -> object:
        return sanitize_snapshot_settings(value)


def adapt_snapshot_v1(snapshot: dict, project: SnapshotProject) -> ProjectSnapshotV2:
    version = snapshot.get("schema_version", 1)
    if version != 1:
        raise ValueError(f"Version de snapshot no soportada: {version}")
    return ProjectSnapshotV2(
        captured_at=datetime.now(UTC),
        project=project,
        diagrams=snapshot.get("diagrams", []),
    )


def upgrade_snapshot_v1_to_v2(
    snapshot: dict,
    project: SnapshotProject,
    *,
    generation_settings: dict[str, Any] | None = None,
    flutter_theme: SnapshotFlutterTheme | None = None,
    ai_settings: SnapshotAiSettings | None = None,
) -> tuple[ProjectSnapshotV2, list[str]]:
    """Upgrade a legacy snapshot in memory without mutating its stored representation."""
    upgraded = adapt_snapshot_v1(snapshot, project)
    upgraded.generation_settings = generation_settings or {}
    upgraded.flutter_theme = flutter_theme
    upgraded.ai_settings = ai_settings
    return upgraded, [
        "snapshot_v1_adapted",
        "missing_settings_completed_from_current_defaults",
    ]


def parse_project_snapshot(snapshot: dict, project: SnapshotProject) -> ProjectSnapshotV2:
    version = snapshot.get("schema_version", 1)
    if version == 1:
        return adapt_snapshot_v1(snapshot, project)
    if version == 2:
        parsed = ProjectSnapshotV2.model_validate(snapshot)
        if parsed.project.id != project.id:
            raise ValueError("El snapshot pertenece a otro proyecto")
        return parsed
    raise ValueError(f"Version de snapshot no soportada: {version}")


def canonicalize_project_snapshot(snapshot: ProjectSnapshotV2 | dict) -> bytes:
    parsed = snapshot if isinstance(snapshot, ProjectSnapshotV2) else ProjectSnapshotV2.model_validate(snapshot)
    value = parsed.model_dump(mode="json", exclude={"captured_at"})
    if value.get("flutter_theme"):
        value["flutter_theme"].pop("revision", None)
    value["diagrams"] = sorted(value.get("diagrams", []), key=lambda item: str(item.get("id", "")))
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def snapshot_sha256(snapshot: ProjectSnapshotV2 | dict) -> str:
    return hashlib.sha256(canonicalize_project_snapshot(snapshot)).hexdigest()

