from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class MensajeIA(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "ai_messages"
    __table_args__ = (
        UniqueConstraint(
            "conversacion_id", "numero_secuencia", name="uq_ai_messages_conversation_sequence"
        ),
        UniqueConstraint(
            "conversacion_id",
            "author_user_id",
            "client_message_id",
            name="uq_ai_messages_client_message",
        ),
        CheckConstraint("role IN ('user','assistant','system','tool')", name="ck_ai_messages_role"),
        CheckConstraint(
            "estado IN ('pending','streaming','completed','failed','cancelled')",
            name="ck_ai_messages_status",
        ),
        CheckConstraint("char_length(content) BETWEEN 1 AND 20000", name="ck_ai_messages_content"),
        CheckConstraint(
            "role <> 'user' OR author_user_id IS NOT NULL",
            name="ck_ai_messages_user_author",
        ),
        Index("ix_ai_messages_project_sequence", "proyecto_id", "numero_secuencia"),
        Index("ix_ai_messages_correlation_id", "correlacion_id"),
        Index("ix_ai_messages_created_id", "fecha_creacion", "id"),
    )

    conversation_id: Mapped[UUID] = mapped_column("conversacion_id",
        PG_UUID(as_uuid=True), ForeignKey("conversaciones_ia.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False
    )
    author_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_number: Mapped[int] = mapped_column("numero_secuencia", Integer, nullable=False)
    client_message_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    correlation_id: Mapped[UUID] = mapped_column("correlacion_id", PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column("estado", String(30), nullable=False, default="completed")
    detected_intents: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    references_json: Mapped[list] = mapped_column("referencias_json", JSONB, nullable=False, default=list)
    metadata_json: Mapped[dict] = mapped_column("metadatos_json", JSONB, nullable=False, default=dict)
