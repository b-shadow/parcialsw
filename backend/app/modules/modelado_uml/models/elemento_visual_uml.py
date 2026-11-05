from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class ElementoVisualUML(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "uml_visual_elements"
    __table_args__ = (
        UniqueConstraint("diagrama_id", "tipo_elemento", "elemento_id", name="uq_visual_element_ref"),
    )

    diagram_id: Mapped[UUID] = mapped_column("diagrama_id",
        PG_UUID(as_uuid=True), ForeignKey("diagramas_uml.id"), index=True
    )
    element_type: Mapped[str] = mapped_column("tipo_elemento", String(50), nullable=False)
    element_id: Mapped[UUID] = mapped_column("elemento_id", PG_UUID(as_uuid=True), nullable=False)
    position_x: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    position_y: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    width: Mapped[float | None] = mapped_column(Float)
    height: Mapped[float | None] = mapped_column(Float)
    style: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

