from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class AiProjectSettings(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_project_settings"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_ai_project_settings_project"),
        CheckConstraint(
            "preferred_provider IN ('ollama','rule_engine')",
            name="ck_ai_project_settings_provider",
        ),
        CheckConstraint(
            "max_context_messages BETWEEN 5 AND 200",
            name="ck_ai_project_settings_max_context",
        ),
        CheckConstraint(
            "summary_trigger_messages BETWEEN 5 AND 200",
            name="ck_ai_project_settings_summary_trigger",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    preferred_provider: Mapped[str] = mapped_column(String(40), nullable=False, default="ollama")
    model_name: Mapped[str] = mapped_column(
        String(120), nullable=False, default="qwen2.5-coder:7b"
    )
    fallback_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    require_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_context_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    summary_trigger_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    settings_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    updated_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
