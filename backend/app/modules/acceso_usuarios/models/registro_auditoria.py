from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class RegistroAuditoria(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "registros_auditoria"

    user_id: Mapped[UUID | None] = mapped_column("usuario_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    project_id: Mapped[UUID | None] = mapped_column("proyecto_id", PG_UUID(as_uuid=True), ForeignKey("proyectos.id"))
    module: Mapped[str] = mapped_column("modulo", String(80), nullable=False, index=True)
    action: Mapped[str] = mapped_column("accion", String(120), nullable=False, index=True)
    result: Mapped[str] = mapped_column("resultado", String(40), nullable=False, default="success")
    detail: Mapped[str | None] = mapped_column("detalle", Text)
    metadata_json: Mapped[dict] = mapped_column("metadatos_json", JSONB, nullable=False, default=dict)
