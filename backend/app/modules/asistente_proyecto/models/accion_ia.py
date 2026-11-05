from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class AccionIA(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "acciones_ia"
    __table_args__ = (
        UniqueConstraint("proyecto_id", "clave_idempotencia", name="uq_acciones_ia_proyecto_id_clave_idempotencia"),
        CheckConstraint("nivel_riesgo IN ('low','medium','high')", name="ck_acciones_ia_nivel_riesgo"),
        CheckConstraint(
            "estado IN ('proposed','confirmed','executing','applied','rejected','failed','cancelled')",
            name="ck_acciones_ia_estado",
        ),
    )

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True),
        ForeignKey("proyectos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[UUID] = mapped_column("conversacion_id",
        PG_UUID(as_uuid=True), ForeignKey("conversaciones_ia.id", ondelete="CASCADE"), nullable=False
    )
    source_message_id: Mapped[UUID] = mapped_column("mensaje_origen_id",
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    requested_by_user_id: Mapped[UUID] = mapped_column("usuario_solicitante_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column("tipo_accion", String(80), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column("tipo_destino", String(80))
    target_id: Mapped[UUID | None] = mapped_column("destino_id", PG_UUID(as_uuid=True))
    payload: Mapped[dict] = mapped_column("carga_datos", JSONB, nullable=False, default=dict)
    risk_level: Mapped[str] = mapped_column("nivel_riesgo", String(20), nullable=False, default="low")
    requires_confirmation: Mapped[bool] = mapped_column("requiere_confirmacion", Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column("estado", String(30), nullable=False, default="proposed")
    confirmed_by_user_id: Mapped[UUID | None] = mapped_column("usuario_confirmador_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id")
    )
    confirmed_at: Mapped[datetime | None] = mapped_column("fecha_confirmacion", DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column("fecha_ejecucion", DateTime(timezone=True))
    result_json: Mapped[dict] = mapped_column("resultado_json", JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column("mensaje_error", Text)
    idempotency_key: Mapped[UUID] = mapped_column("clave_idempotencia", PG_UUID(as_uuid=True), nullable=False)
