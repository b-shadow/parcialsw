from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class InvitacionProyecto(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "invitaciones_proyecto"
    __table_args__ = (
        Index(
            "ix_invitaciones_proyecto_proyecto_id_2",
            "proyecto_id",
            text("lower(correo_invitado)"),
            unique=True,
            postgresql_where=text("estado = 'pending'"),
        ),
    )

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id"), index=True
    )
    invited_by_user_id: Mapped[UUID] = mapped_column("usuario_invitador_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    invited_user_id: Mapped[UUID | None] = mapped_column("usuario_invitado_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    invited_email: Mapped[str] = mapped_column("correo_invitado", String(180), nullable=False, index=True)
    project_role: Mapped[str] = mapped_column("rol_proyecto", String(40), nullable=False)
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False, default="pending", index=True)
    expires_at: Mapped[datetime | None] = mapped_column("fecha_expiracion", DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column("fecha_respuesta", DateTime(timezone=True))
