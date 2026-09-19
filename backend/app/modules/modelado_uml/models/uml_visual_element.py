from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import TimestampMixin, UuidPrimaryKeyMixin
from app.core.database.session import Base


class UmlVisualElement(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "uml_visual_elements"
    __table_args__ = (
        UniqueConstraint("diagram_id", "element_type", "element_id", name="uq_visual_element_ref"),
    )

    diagram_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_diagrams.id"), index=True
    )
    element_type: Mapped[str] = mapped_column(String(50), nullable=False)
    element_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    position_y: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    width: Mapped[float | None] = mapped_column(Float)
    height: Mapped[float | None] = mapped_column(Float)
    style: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

