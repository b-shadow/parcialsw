from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class EventoBandejaSalidaNoSQL(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "bandeja_salida_nosql"
    __table_args__ = (
        UniqueConstraint("clave_idempotencia", name="uq_bandeja_salida_nosql_clave_idempotencia"),
        CheckConstraint(
            "estado IN ('pending', 'processing', 'completed', 'retry', 'dead')",
            name="ck_bandeja_salida_nosql_estado",
        ),
        Index("ix_bandeja_salida_nosql_estado_fecha_disponible", "estado", "fecha_disponible"),
        Index("ix_bandeja_salida_nosql_tipo_agregado_agregado_id", "tipo_agregado", "agregado_id"),
    )

    aggregate_type: Mapped[str] = mapped_column("tipo_agregado", String(80), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column("agregado_id", PG_UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column("tipo_evento", String(100), nullable=False)
    payload: Mapped[dict] = mapped_column("carga_datos", JSONB, nullable=False)
    idempotency_key: Mapped[str] = mapped_column("clave_idempotencia", String(200), nullable=False)
    status: Mapped[str] = mapped_column("estado", String(24), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column("numero_intentos", Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column("fecha_disponible", DateTime(timezone=True), nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column("fecha_bloqueo", DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column("bloqueado_por", String(120))
    processed_at: Mapped[datetime | None] = mapped_column("fecha_procesamiento", DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column("ultimo_error", Text)
