from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.acceso_usuarios.models.rol_usuario import RolUsuario
    from app.modules.acceso_usuarios.models.sesion import SesionUsuario


class Usuario(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "usuarios"

    full_name: Mapped[str] = mapped_column("nombre_completo", String(150), nullable=False)
    email: Mapped[str] = mapped_column("correo", String(180), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column("hash_contrasena", String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column("esta_activo", Boolean, nullable=False, default=True)
    last_access_at: Mapped[datetime | None] = mapped_column("fecha_ultimo_acceso", DateTime(timezone=True))

    roles: Mapped[list[RolUsuario]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list[SesionUsuario]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def nombres_roles(self) -> list[str]:
        return sorted(user_role.role.name for user_role in self.roles if user_role.role is not None)
