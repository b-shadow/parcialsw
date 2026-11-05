from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class Notificacion(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "notificaciones"
    __table_args__ = (
        UniqueConstraint("usuario_destinatario_id", "clave_deduplicacion", name="uq_notificaciones_usuario_destinatario_id_clave_deduplicacion"),
        CheckConstraint(
            "severidad IN ('info', 'success', 'warning', 'error')",
            name="ck_notificaciones_severidad",
        ),
        Index("ix_notificaciones_usuario_destinatario_id_fecha_suceso", "usuario_destinatario_id", "fecha_suceso"),
        Index("ix_notificaciones_usuario_destinatario_id_fecha_lectura", "usuario_destinatario_id", "fecha_lectura"),
    )

    recipient_user_id: Mapped[UUID] = mapped_column("usuario_destinatario_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE")
    )
    project_id: Mapped[UUID | None] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), index=True
    )
    actor_user_id: Mapped[UUID | None] = mapped_column("usuario_actor_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    type: Mapped[str] = mapped_column("tipo", String(80), nullable=False, index=True)
    severity: Mapped[str] = mapped_column("severidad", String(16), nullable=False, default="info")
    title: Mapped[str] = mapped_column("titulo", String(180), nullable=False)
    body: Mapped[str] = mapped_column("cuerpo", String(500), nullable=False)
    resource_type: Mapped[str | None] = mapped_column("tipo_recurso", String(80))
    resource_id: Mapped[UUID | None] = mapped_column("recurso_id", PG_UUID(as_uuid=True))
    deep_link: Mapped[dict] = mapped_column("enlace_directo", JSONB, nullable=False, default=dict)
    dedup_key: Mapped[str] = mapped_column("clave_deduplicacion", String(200), nullable=False)
    group_key: Mapped[str | None] = mapped_column("clave_grupo", String(200), index=True)
    occurred_at: Mapped[datetime] = mapped_column("fecha_suceso", DateTime(timezone=True), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column("fecha_lectura", DateTime(timezone=True))
    clicked_at: Mapped[datetime | None] = mapped_column("fecha_clic", DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column("fecha_archivo", DateTime(timezone=True))
