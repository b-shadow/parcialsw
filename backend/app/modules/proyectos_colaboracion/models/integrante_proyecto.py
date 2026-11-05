from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.proyectos_colaboracion.models.proyecto import Proyecto


class IntegranteProyecto(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "integrantes_proyecto"
    __table_args__ = (UniqueConstraint("proyecto_id", "usuario_id", name="uq_integrantes_proyecto_proyecto_id_usuario_id"),)

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id"), index=True
    )
    user_id: Mapped[UUID] = mapped_column("usuario_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True)
    project_role: Mapped[str] = mapped_column("rol_proyecto", String(40), nullable=False, index=True)
    joined_at: Mapped[datetime | None] = mapped_column("fecha_incorporacion", DateTime(timezone=True))

    project: Mapped[Proyecto] = relationship(back_populates="members")
