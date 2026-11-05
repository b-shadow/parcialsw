from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class ArtefactoGenerado(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "artefactos_generados"

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id"), index=True
    )
    generated_backend_id: Mapped[UUID | None] = mapped_column("backend_generado_id",
        PG_UUID(as_uuid=True), ForeignKey("backends_generados.id")
    )
    generated_frontend_id: Mapped[UUID | None] = mapped_column("frontend_generado_id",
        PG_UUID(as_uuid=True), ForeignKey("frontends_generados.id")
    )
    artifact_type: Mapped[str] = mapped_column("tipo_artefacto", String(60), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column("nombre_archivo", String(255), nullable=False)
    file_path: Mapped[str] = mapped_column("ruta_archivo", String(500), nullable=False)
    checksum: Mapped[str | None] = mapped_column("suma_verificacion", String(128))
    metadata_json: Mapped[dict] = mapped_column("metadatos_json", JSONB, nullable=False, default=dict)
