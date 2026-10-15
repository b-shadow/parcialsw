from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class CollaborationEvent(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "collaboration_events"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "sequence_number", name="uq_collaboration_events_project_sequence"
        ),
        UniqueConstraint(
            "project_id",
            "user_id",
            "client_event_id",
            name="uq_collaboration_events_client_event",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    diagram_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("uml_diagrams.id"))
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    client_event_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    element_type: Mapped[str | None] = mapped_column(String(80))
    element_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    base_version: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

