from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.acceso_usuarios.models import Usuario


class SuscripcionPush(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "suscripciones_push"
    __table_args__ = (UniqueConstraint("punto_acceso", name="uq_suscripciones_push_punto_acceso"),)

    user_id: Mapped[UUID] = mapped_column("usuario_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column("punto_acceso", String(2048), nullable=False)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column("autenticacion", Text, nullable=False)
    content_encoding: Mapped[str] = mapped_column("codificacion_contenido", String(40), nullable=False, default="aes128gcm")
    user_agent: Mapped[str | None] = mapped_column("agente_usuario", String(512))
    expires_at: Mapped[datetime | None] = mapped_column("fecha_expiracion", DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column("esta_activo", Boolean, nullable=False, default=True)
    failure_count: Mapped[int] = mapped_column("numero_fallos", Integer, nullable=False, default=0)
    last_success_at: Mapped[datetime | None] = mapped_column("fecha_ultimo_exito", DateTime(timezone=True))

    user: Mapped[Usuario] = relationship()
