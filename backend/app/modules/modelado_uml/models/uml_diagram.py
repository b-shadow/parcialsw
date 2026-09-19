from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.uml_class import UmlClass
    from app.modules.modelado_uml.models.uml_relationship import UmlRelationship


class UmlDiagram(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uml_diagrams"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), index=True
    )
    created_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    diagram_type: Mapped[str] = mapped_column(String(50), nullable=False, default="class")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active", index=True)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    classes: Mapped[list[UmlClass]] = relationship(
        back_populates="diagram", cascade="all, delete-orphan"
    )
    relationships: Mapped[list[UmlRelationship]] = relationship(
        back_populates="diagram", cascade="all, delete-orphan"
    )
