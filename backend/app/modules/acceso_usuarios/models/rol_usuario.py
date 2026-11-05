from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.acceso_usuarios.models.rol import Rol
    from app.modules.acceso_usuarios.models.usuario import Usuario


class RolUsuario(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "roles_usuario"
    __table_args__ = (UniqueConstraint("usuario_id", name="uq_roles_usuario_usuario_id"),)

    user_id: Mapped[UUID] = mapped_column("usuario_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True)
    role_id: Mapped[UUID] = mapped_column("rol_id", PG_UUID(as_uuid=True), ForeignKey("roles.id"), index=True)

    user: Mapped[Usuario] = relationship(back_populates="roles")
    role: Mapped[Rol] = relationship(back_populates="user_roles")
