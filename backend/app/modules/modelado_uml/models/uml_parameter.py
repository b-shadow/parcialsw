from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.uml_method import UmlMethod


class UmlParameter(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uml_parameters"

    method_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_methods.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    data_type: Mapped[str] = mapped_column(String(120), nullable=False)
    default_value: Mapped[str | None] = mapped_column(String(255))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    method: Mapped[UmlMethod] = relationship(back_populates="parameters")
