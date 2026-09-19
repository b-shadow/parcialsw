from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.uml_class import UmlClass
    from app.modules.modelado_uml.models.uml_parameter import UmlParameter


class UmlMethod(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uml_methods"

    class_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_classes.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    return_type: Mapped[str | None] = mapped_column(String(120))
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    uml_class: Mapped[UmlClass] = relationship(back_populates="methods")
    parameters: Mapped[list[UmlParameter]] = relationship(
        back_populates="method", cascade="all, delete-orphan"
    )
