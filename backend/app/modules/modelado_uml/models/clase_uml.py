from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.atributo_uml import AtributoUML
    from app.modules.modelado_uml.models.diagrama_uml import DiagramaUML
    from app.modules.modelado_uml.models.metodo_uml import MetodoUML


class ClaseUML(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "uml_classes"

    diagram_id: Mapped[UUID] = mapped_column("diagrama_id",
        PG_UUID(as_uuid=True), ForeignKey("diagramas_uml.id"), index=True
    )
    name: Mapped[str] = mapped_column("nombre", String(120), nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    element_type: Mapped[str] = mapped_column("tipo_elemento", String(40), nullable=False, default="class")
    stereotype: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column("descripcion", Text)
    metadata_json: Mapped[dict] = mapped_column("metadatos_json", JSONB, nullable=False, default=dict)

    diagram: Mapped[DiagramaUML] = relationship(back_populates="classes")
    attributes: Mapped[list[AtributoUML]] = relationship(
        back_populates="uml_class", cascade="all, delete-orphan"
    )
    methods: Mapped[list[MetodoUML]] = relationship(
        back_populates="uml_class", cascade="all, delete-orphan"
    )
