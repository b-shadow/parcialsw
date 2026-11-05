from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.clase_uml import ClaseUML
    from app.modules.modelado_uml.models.relacion_uml import RelacionUML


class DiagramaUML(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "diagramas_uml"
    __table_args__ = (
        CheckConstraint(
            "almacenamiento_contenido = 'mongodb'",
            name="ck_diagramas_uml_almacenamiento_contenido",
        ),
        Index("ix_diagramas_uml_fecha_actualizacion_id", "fecha_actualizacion", "id"),
    )

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id"), index=True
    )
    created_by_user_id: Mapped[UUID] = mapped_column("usuario_creador_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    name: Mapped[str] = mapped_column("nombre", String(160), nullable=False)
    diagram_type: Mapped[str] = mapped_column("tipo_diagrama", String(50), nullable=False, default="class")
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False, default="active", index=True)
    current_version: Mapped[int] = mapped_column("version_actual", Integer, nullable=False, default=1)
    description: Mapped[str | None] = mapped_column("descripcion", Text)
    metadata_json: Mapped[dict] = mapped_column("metadatos_json", JSONB, nullable=False, default=dict)
    content_storage: Mapped[str] = mapped_column("almacenamiento_contenido",
        String(20), nullable=False, default="mongodb", server_default="mongodb"
    )

    classes: Mapped[list[ClaseUML]] = relationship(
        back_populates="diagram", cascade="all, delete-orphan"
    )
    relationships: Mapped[list[RelacionUML]] = relationship(
        back_populates="diagram", cascade="all, delete-orphan"
    )
