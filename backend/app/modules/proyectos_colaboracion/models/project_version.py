from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base

if TYPE_CHECKING:
    from app.modules.proyectos_colaboracion.models.project import Project


class ProjectVersion(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_versions"
    __table_args__ = (
        UniqueConstraint("project_id", "version_number", name="uq_project_versions_project_number"),
        UniqueConstraint(
            "project_id",
            "created_by_user_id",
            "idempotency_key",
            name="uq_project_versions_idempotency",
        ),
        CheckConstraint("version_number > 0", name="ck_project_versions_number_positive"),
        CheckConstraint("snapshot_schema_version > 0", name="ck_project_versions_schema_positive"),
        CheckConstraint(
            "snapshot_storage = 'mongodb'",
            name="ck_project_versions_snapshot_storage",
        ),
        CheckConstraint(
            "kind IN ('manual', 'pre_restore_backup')",
            name="ck_project_versions_kind",
        ),
        Index("ix_project_versions_project_created", "project_id", "created_at"),
        Index("ix_project_versions_created_id", "created_at", "id"),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    created_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="saved")
    kind: Mapped[str] = mapped_column(String(40), nullable=False, default="manual", index=True)
    snapshot_schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    snapshot_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    project_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String(120))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    snapshot_storage: Mapped[str] = mapped_column(
        String(20), nullable=False, default="mongodb", server_default="mongodb"
    )

    project: Mapped[Project] = relationship(back_populates="versions")
