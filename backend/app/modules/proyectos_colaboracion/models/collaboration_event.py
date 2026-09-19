from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class CollaborationEvent(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "collaboration_events"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    diagram_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("uml_diagrams.id"))
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    element_type: Mapped[str | None] = mapped_column(String(80))
    element_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    base_version: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

