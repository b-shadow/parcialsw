from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class TransformacionUML(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "transformaciones_uml"

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id"), index=True
    )
    diagram_id: Mapped[UUID] = mapped_column("diagrama_id",
        PG_UUID(as_uuid=True), ForeignKey("diagramas_uml.id"), index=True
    )
    requested_by_user_id: Mapped[UUID] = mapped_column("usuario_solicitante_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True
    )
    source_version: Mapped[str | None] = mapped_column("version_origen", String(80))
    target_platform: Mapped[str] = mapped_column("plataforma_destino", String(80), nullable=False)
    intermediate_model: Mapped[dict] = mapped_column("modelo_intermedio", JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False, default="pending", index=True)
    error_detail: Mapped[str | None] = mapped_column("detalle_error", Text)
