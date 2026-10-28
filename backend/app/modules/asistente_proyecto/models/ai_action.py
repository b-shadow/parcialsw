from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class AiAction(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_actions"
    __table_args__ = (
        UniqueConstraint("project_id", "idempotency_key", name="uq_ai_actions_idempotency"),
        CheckConstraint("risk_level IN ('low','medium','high')", name="ck_ai_actions_risk"),
        CheckConstraint(
            "status IN ('proposed','confirmed','executing','applied','rejected','failed','cancelled')",
            name="ck_ai_actions_status",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False
    )
    source_message_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    requested_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(80))
    target_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="proposed")
    confirmed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id")
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
