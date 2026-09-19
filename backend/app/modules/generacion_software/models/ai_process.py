from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class AiProcess(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_processes"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    project_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id"))
    diagram_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("uml_diagrams.id"))
    process_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    model_provider: Mapped[str] = mapped_column(String(80), nullable=False, default="local")
    model_name: Mapped[str | None] = mapped_column(String(120))
    input_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending", index=True)
    error_detail: Mapped[str | None] = mapped_column(Text)

