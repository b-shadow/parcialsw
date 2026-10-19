from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class FlutterThemeSettings(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "flutter_theme_settings"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_flutter_theme_settings_project"),
        CheckConstraint("schema_version > 0", name="ck_flutter_theme_settings_schema_version"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    preset_name: Mapped[str | None] = mapped_column(String(120))
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    updated_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )


class FlutterThemePreset(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "flutter_theme_presets"
    __table_args__ = (
        Index("uq_flutter_theme_preset_project_name_ci", "project_id", text("lower(name)"), unique=True),
        CheckConstraint("schema_version > 0", name="ck_flutter_theme_preset_schema_version"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    created_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
