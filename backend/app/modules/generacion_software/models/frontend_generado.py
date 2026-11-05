from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class FrontendGenerado(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "frontends_generados"

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id"), index=True
    )
    transformation_id: Mapped[UUID] = mapped_column("transformacion_id",
        PG_UUID(as_uuid=True), ForeignKey("transformaciones_uml.id"), index=True
    )
    generated_by_user_id: Mapped[UUID] = mapped_column("usuario_generador_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True
    )
    backend_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backends_generados.id")
    )
    name: Mapped[str] = mapped_column("nombre", String(160), nullable=False)
    technology: Mapped[str] = mapped_column("tecnologia", String(80), nullable=False, default="Flutter")
    language: Mapped[str] = mapped_column("lenguaje", String(40), nullable=False, default="Dart")
    version_label: Mapped[str] = mapped_column("etiqueta_version", String(80), nullable=False)
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False, default="generated", index=True)
    artifact_path: Mapped[str | None] = mapped_column("ruta_artefacto", String(500))
    manifest: Mapped[dict] = mapped_column("manifiesto", JSONB, nullable=False, default=dict)
    error_detail: Mapped[str | None] = mapped_column("detalle_error", Text)
