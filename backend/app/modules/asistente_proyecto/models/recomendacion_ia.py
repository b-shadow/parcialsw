from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class RecomendacionIA(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "recomendaciones_ia"
    __table_args__ = (
        CheckConstraint(
            "severidad IN ('info','warning','critical')", name="ck_recomendaciones_ia_severidad"
        ),
        CheckConstraint(
            "estado IN ('open','accepted','dismissed','resolved')",
            name="ck_recomendaciones_ia_estado",
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
    category: Mapped[str] = mapped_column("categoria", String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column("severidad", String(20), nullable=False, default="info")
    title: Mapped[str] = mapped_column("titulo", String(200), nullable=False)
    description: Mapped[str] = mapped_column("descripcion", Text, nullable=False)
    references_json: Mapped[list] = mapped_column("referencias_json", JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column("estado", String(30), nullable=False, default="open")
    resolved_by_user_id: Mapped[UUID | None] = mapped_column("usuario_resolutor_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id")
    )
    resolved_at: Mapped[datetime | None] = mapped_column("fecha_resolucion", DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column("nota_resolucion", Text)
