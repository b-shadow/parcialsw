from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.acceso_usuarios.models.usuario import Usuario


class SesionUsuario(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "sesiones_usuario"

    user_id: Mapped[UUID] = mapped_column("usuario_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True)
    refresh_token_hash: Mapped[str | None] = mapped_column("hash_token_renovacion", String(255))
    ip_address: Mapped[str | None] = mapped_column("direccion_ip", String(80))
    user_agent: Mapped[str | None] = mapped_column("agente_usuario", String(255))
    revoked_at: Mapped[datetime | None] = mapped_column("fecha_revocacion", DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column("fecha_expiracion", DateTime(timezone=True), nullable=False)

    user: Mapped[Usuario] = relationship(back_populates="sessions")
