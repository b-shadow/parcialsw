from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class GeneratedBackend(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generated_backends"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    transformation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_transformations.id"), index=True
    )
    generated_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    technology: Mapped[str] = mapped_column(String(80), nullable=False, default="Spring Boot")
    language: Mapped[str] = mapped_column(String(40), nullable=False, default="Java")
    database_engine: Mapped[str] = mapped_column(String(80), nullable=False, default="PostgreSQL")
    version_label: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="generated", index=True)
    artifact_path: Mapped[str | None] = mapped_column(String(500))
    manifest: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_detail: Mapped[str | None] = mapped_column(Text)

