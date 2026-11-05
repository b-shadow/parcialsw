from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class ConversacionIA(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "conversaciones_ia"
    __table_args__ = (
        CheckConstraint("estado IN ('active','archived')", name="ck_conversaciones_ia_estado"),
        CheckConstraint("resumen_hasta_secuencia >= 0", name="ck_conversaciones_ia_resumen_hasta_secuencia"),
        CheckConstraint("secuencia_ultimo_mensaje >= 0", name="ck_conversaciones_ia_secuencia_ultimo_mensaje"),
        CheckConstraint("version_esquema > 0", name="ck_conversaciones_ia_version_esquema"),
        CheckConstraint(
            "almacenamiento_mensajes = 'mongodb'",
            name="ck_conversaciones_ia_almacenamiento_mensajes",
        ),
        Index("ix_conversaciones_ia_proyecto_id_fecha_actualizacion", "proyecto_id", "fecha_actualizacion"),
    )
    title: Mapped[str] = mapped_column("titulo", String(160), nullable=False, default="Nuevo chat")
    created_by_user_id: Mapped[UUID | None] = mapped_column("usuario_creador_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True),
        ForeignKey("proyectos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column("estado", String(30), nullable=False, default="active")
    summary: Mapped[str | None] = mapped_column("resumen", Text)
    summary_until_sequence: Mapped[int] = mapped_column("resumen_hasta_secuencia", Integer, nullable=False, default=0)
    last_message_sequence: Mapped[int] = mapped_column("secuencia_ultimo_mensaje", Integer, nullable=False, default=0)
    schema_version: Mapped[int] = mapped_column("version_esquema", Integer, nullable=False, default=1)
    message_storage: Mapped[str] = mapped_column("almacenamiento_mensajes",
        String(20), nullable=False, default="mongodb", server_default="mongodb"
    )
