from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class ProcesoIA(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "procesos_ia"

    user_id: Mapped[UUID] = mapped_column("usuario_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True)
    project_id: Mapped[UUID | None] = mapped_column("proyecto_id", PG_UUID(as_uuid=True), ForeignKey("proyectos.id"))
    diagram_id: Mapped[UUID | None] = mapped_column("diagrama_id", PG_UUID(as_uuid=True), ForeignKey("diagramas_uml.id"))
    process_type: Mapped[str] = mapped_column("tipo_proceso", String(80), nullable=False, index=True)
    model_provider: Mapped[str] = mapped_column("proveedor_modelo", String(80), nullable=False, default="local")
    model_name: Mapped[str | None] = mapped_column("nombre_modelo", String(120))
    input_payload: Mapped[dict] = mapped_column("carga_entrada", JSONB, nullable=False, default=dict)
    output_payload: Mapped[dict] = mapped_column("carga_salida", JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False, default="pending", index=True)
    error_detail: Mapped[str | None] = mapped_column("detalle_error", Text)
