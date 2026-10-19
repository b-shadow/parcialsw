from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.uml_method import UmlMethod


class UmlMethodSpecification(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uml_method_specifications"
    __table_args__ = (
        UniqueConstraint("method_id", name="uq_uml_method_specifications_method"),
        CheckConstraint(
            "operation_kind IN ('create','read','update','delete','search','calculate','business_action','custom')",
            name="ck_uml_method_specifications_operation_kind",
        ),
        CheckConstraint(
            "exposure IN ('internal','api','user_action')",
            name="ck_uml_method_specifications_exposure",
        ),
        CheckConstraint("schema_version > 0", name="ck_uml_method_specifications_schema_version"),
        CheckConstraint("revision > 0", name="ck_uml_method_specifications_revision"),
    )

    method_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("uml_methods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    operation_kind: Mapped[str] = mapped_column(String(40), nullable=False, default="custom")
    exposure: Mapped[str] = mapped_column(String(30), nullable=False, default="internal")
    preconditions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    postconditions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    business_rules: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    validations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    side_effects: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    required_permissions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    related_entities: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    backend_contract: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    frontend_contract: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    method: Mapped[UmlMethod] = relationship(back_populates="specification")
