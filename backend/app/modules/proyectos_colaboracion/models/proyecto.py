from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.configuracion_proyecto import ConfiguracionProyectoJSON
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.proyectos_colaboracion.models.integrante_proyecto import IntegranteProyecto
    from app.modules.proyectos_colaboracion.models.version_proyecto import VersionProyecto


class Proyecto(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "proyectos"

    owner_id: Mapped[UUID] = mapped_column("propietario_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True)
    name: Mapped[str] = mapped_column("nombre", String(160), nullable=False)
    description: Mapped[str | None] = mapped_column("descripcion", Text)
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False, default="active", index=True)
    settings: Mapped[dict] = mapped_column("configuracion", ConfiguracionProyectoJSON(), nullable=False, default=dict)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    siguiente_numero_version: Mapped[int] = mapped_column("siguiente_numero_version", Integer, nullable=False, default=1)

    members: Mapped[list[IntegranteProyecto]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    versions: Mapped[list[VersionProyecto]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
