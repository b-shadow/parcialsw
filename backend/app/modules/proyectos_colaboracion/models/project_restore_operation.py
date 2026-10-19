from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class ProjectRestoreOperation(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_restore_operations"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "requested_by_user_id", "idempotency_key",
            name="uq_project_restore_idempotency",
        ),
        CheckConstraint(
            "status IN ('validating', 'completed', 'failed')",
            name="ck_project_restore_status",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    source_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("project_versions.id")
    )
    backup_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("project_versions.id")
    )
    requested_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="validating")
    source_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    before_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    after_snapshot_hash: Mapped[str | None] = mapped_column(String(64))
    project_revision_before: Mapped[int] = mapped_column(Integer, nullable=False)
    project_revision_after: Mapped[int | None] = mapped_column(Integer)
    diagnostics_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
