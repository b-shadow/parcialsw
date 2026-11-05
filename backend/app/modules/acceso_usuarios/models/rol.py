from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.acceso_usuarios.models.rol_usuario import RolUsuario


class Rol(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column("nombre", String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column("descripcion", Text)
    is_system: Mapped[bool] = mapped_column("es_sistema", Boolean, nullable=False, default=True)

    user_roles: Mapped[list[RolUsuario]] = relationship(back_populates="role")
