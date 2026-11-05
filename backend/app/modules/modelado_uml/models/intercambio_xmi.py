from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class IntercambioXMI(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "intercambios_xmi"

    diagram_id: Mapped[UUID] = mapped_column("diagrama_id",
        PG_UUID(as_uuid=True), ForeignKey("diagramas_uml.id"), index=True
    )
    user_id: Mapped[UUID] = mapped_column("usuario_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True)
    exchange_type: Mapped[str] = mapped_column("tipo_intercambio", String(30), nullable=False, index=True)
    tool_name: Mapped[str | None] = mapped_column("nombre_herramienta", String(120))
    file_name: Mapped[str] = mapped_column("nombre_archivo", String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column("ruta_archivo", String(500))
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False, default="completed", index=True)
    error_detail: Mapped[str | None] = mapped_column("detalle_error", Text)
    metadata_json: Mapped[dict] = mapped_column("metadatos_json", JSONB, nullable=False, default=dict)
