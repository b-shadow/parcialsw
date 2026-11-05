from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class BandejaSalidaNotificacion(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "bandeja_salida_notificaciones"
    __table_args__ = (
        UniqueConstraint("notificacion_id", "canal", name="uq_bandeja_salida_notificaciones_notificacion_id_canal"),
        CheckConstraint(
            "estado IN ('pending', 'processing', 'delivered', 'retry', 'dead')",
            name="ck_bandeja_salida_notificaciones_estado",
        ),
        Index("ix_bandeja_salida_notificaciones_estado_fecha_disponible", "estado", "fecha_disponible"),
    )

    notification_id: Mapped[UUID] = mapped_column("notificacion_id",
        PG_UUID(as_uuid=True), ForeignKey("notificaciones.id", ondelete="CASCADE")
    )
    channel: Mapped[str] = mapped_column("canal", String(32), nullable=False, default="web_push")
    status: Mapped[str] = mapped_column("estado", String(24), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column("numero_intentos", Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column("fecha_disponible", DateTime(timezone=True), nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column("fecha_bloqueo", DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column("bloqueado_por", String(120))
    last_error_code: Mapped[str | None] = mapped_column("codigo_ultimo_error", String(120))
    delivered_at: Mapped[datetime | None] = mapped_column("fecha_entrega", DateTime(timezone=True))
