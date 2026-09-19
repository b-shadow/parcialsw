from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.uml_class import UmlClass


class UmlAttribute(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uml_attributes"

    class_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_classes.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    data_type: Mapped[str] = mapped_column(String(120), nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="private")
    initial_value: Mapped[str | None] = mapped_column(String(255))
    multiplicity: Mapped[str | None] = mapped_column(String(40))
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    constraints: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    uml_class: Mapped[UmlClass] = relationship(back_populates="attributes")
