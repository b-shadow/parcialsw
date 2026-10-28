from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class AiConversation(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_conversations"
    __table_args__ = (
        CheckConstraint("status IN ('active','archived')", name="ck_ai_conversations_status"),
        CheckConstraint("summary_until_sequence >= 0", name="ck_ai_conversations_summary_sequence"),
        CheckConstraint("last_message_sequence >= 0", name="ck_ai_conversations_last_sequence"),
        CheckConstraint("schema_version > 0", name="ck_ai_conversations_schema_version"),
        CheckConstraint(
            "message_storage = 'mongodb'",
            name="ck_ai_conversations_message_storage",
        ),
        Index("ix_ai_conversations_project_updated", "project_id", "updated_at"),
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False, default="Nuevo chat")
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    summary: Mapped[str | None] = mapped_column(Text)
    summary_until_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_message_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    message_storage: Mapped[str] = mapped_column(
        String(20), nullable=False, default="mongodb", server_default="mongodb"
    )
