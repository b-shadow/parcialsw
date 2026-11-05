from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class RestauracionProyecto(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "restauraciones_proyecto"
    __table_args__ = (
        UniqueConstraint(
            "proyecto_id", "usuario_solicitante_id", "clave_idempotencia",
            name="uq_restauraciones_proyecto_proyecto_id_usuario_solicit_f059d2db",
        ),
        CheckConstraint(
            "estado IN ('validating', 'completed', 'failed')",
            name="ck_restauraciones_proyecto_estado",
        ),
    )

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), index=True
    )
    source_version_id: Mapped[UUID] = mapped_column("version_origen_id",
        PG_UUID(as_uuid=True), ForeignKey("versiones_proyecto.id")
    )
    backup_version_id: Mapped[UUID | None] = mapped_column("version_respaldo_id",
        PG_UUID(as_uuid=True), ForeignKey("versiones_proyecto.id")
    )
    requested_by_user_id: Mapped[UUID] = mapped_column("usuario_solicitante_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True
    )
    idempotency_key: Mapped[str] = mapped_column("clave_idempotencia", String(120), nullable=False)
    status: Mapped[str] = mapped_column("estado", String(24), nullable=False, default="validating")
    source_snapshot_hash: Mapped[str] = mapped_column("hash_instantanea_origen", String(64), nullable=False)
    before_snapshot_hash: Mapped[str] = mapped_column("hash_instantanea_anterior", String(64), nullable=False, default="")
    after_snapshot_hash: Mapped[str | None] = mapped_column("hash_instantanea_posterior", String(64))
    project_revision_before: Mapped[int] = mapped_column("revision_proyecto_anterior", Integer, nullable=False)
    project_revision_after: Mapped[int | None] = mapped_column("revision_proyecto_posterior", Integer)
    diagnostics_json: Mapped[dict] = mapped_column("diagnosticos_json", JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column("fecha_inicio", DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column("fecha_finalizacion", DateTime(timezone=True))
