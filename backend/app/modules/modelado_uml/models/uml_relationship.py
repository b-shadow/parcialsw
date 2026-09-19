from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.uml_diagram import UmlDiagram


class UmlRelationship(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uml_relationships"

    diagram_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_diagrams.id"), index=True
    )
    source_class_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_classes.id"), index=True
    )
    target_class_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_classes.id"), index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_cardinality: Mapped[str | None] = mapped_column(String(40))
    target_cardinality: Mapped[str | None] = mapped_column(String(40))
    direction: Mapped[str] = mapped_column(String(40), nullable=False, default="source_to_target")
    label: Mapped[str | None] = mapped_column(String(120))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    diagram: Mapped[UmlDiagram] = relationship(back_populates="relationships")
