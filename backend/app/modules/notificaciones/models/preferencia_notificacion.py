from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class PreferenciaNotificacion(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "preferencias_notificaciones"
    __table_args__ = (
        UniqueConstraint("usuario_id", "proyecto_id", "categoria", name="uq_preferencias_notificaciones_usuario_id_proyecto_id_categoria"),
        Index(
            "ix_preferencias_notificaciones_usuario_id_categoria",
            "usuario_id",
            "categoria",
            unique=True,
            postgresql_where=text("proyecto_id IS NULL"),
        ),
    )

    user_id: Mapped[UUID] = mapped_column("usuario_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[UUID | None] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE")
    )
    category: Mapped[str] = mapped_column("categoria", String(80), nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column("habilitado_en_aplicacion", Boolean, nullable=False, default=True)
    push_enabled: Mapped[bool] = mapped_column("push_habilitado", Boolean, nullable=False, default=True)
    muted_until: Mapped[datetime | None] = mapped_column("silenciado_hasta", DateTime(timezone=True))
