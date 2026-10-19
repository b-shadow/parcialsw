from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class CoordinatedGeneration(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "coordinated_generations"
    __table_args__ = (
        UniqueConstraint(
            "transformation_id",
            "requested_by_user_id",
            "client_request_id",
            name="uq_coordinated_generation_idempotency",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    transformation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_transformations.id"), index=True
    )
    requested_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    backend_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("generated_backends.id")
    )
    frontend_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("generated_frontends.id")
    )
    client_request_id: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    plan_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    plan_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    diagnostics: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    manifest: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    artifact_path: Mapped[str | None] = mapped_column(String(500))
    error_detail: Mapped[str | None] = mapped_column(Text)
