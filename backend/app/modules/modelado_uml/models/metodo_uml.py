from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.modelado_uml.models.clase_uml import ClaseUML
    from app.modules.modelado_uml.models.especificacion_metodo_uml import EspecificacionMetodoUML
    from app.modules.modelado_uml.models.parametro_uml import ParametroUML


class MetodoUML(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "uml_methods"

    class_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("uml_classes.id"), index=True
    )
    name: Mapped[str] = mapped_column("nombre", String(120), nullable=False)
    return_type: Mapped[str | None] = mapped_column(String(120))
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column("metadatos_json", JSONB, nullable=False, default=dict)

    uml_class: Mapped[ClaseUML] = relationship(back_populates="methods")
    parameters: Mapped[list[ParametroUML]] = relationship(
        back_populates="method", cascade="all, delete-orphan"
    )
    specification: Mapped[EspecificacionMetodoUML | None] = relationship(
        back_populates="method", cascade="all, delete-orphan", uselist=False
    )
