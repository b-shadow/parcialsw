from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.uml_attribute import UmlAttribute
    from app.modules.modelado_uml.models.uml_diagram import UmlDiagram
    from app.modules.modelado_uml.models.uml_method import UmlMethod


class UmlClass(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uml_classes"

    diagram_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_diagrams.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    element_type: Mapped[str] = mapped_column(String(40), nullable=False, default="class")
    stereotype: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    diagram: Mapped[UmlDiagram] = relationship(back_populates="classes")
    attributes: Mapped[list[UmlAttribute]] = relationship(
        back_populates="uml_class", cascade="all, delete-orphan"
    )
    methods: Mapped[list[UmlMethod]] = relationship(
        back_populates="uml_class", cascade="all, delete-orphan"
    )
