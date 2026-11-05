from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class GeneracionCoordinada(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "generaciones_coordinadas"
    __table_args__ = (
        UniqueConstraint(
            "transformacion_id",
            "usuario_solicitante_id",
            "solicitud_cliente_id",
            name="uq_generaciones_coordinadas_transformacion_id_usuario__7d4516a9",
        ),
    )

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id"), index=True
    )
    transformation_id: Mapped[UUID] = mapped_column("transformacion_id",
        PG_UUID(as_uuid=True), ForeignKey("transformaciones_uml.id"), index=True
    )
    requested_by_user_id: Mapped[UUID] = mapped_column("usuario_solicitante_id",
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True
    )
    backend_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("backends_generados.id")
    )
    frontend_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("frontends_generados.id")
    )
    client_request_id: Mapped[str] = mapped_column("solicitud_cliente_id", String(120), nullable=False)
    name: Mapped[str] = mapped_column("nombre", String(160), nullable=False)
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False, index=True)
    stage: Mapped[str] = mapped_column("etapa", String(40), nullable=False)
    plan_hash: Mapped[str | None] = mapped_column("hash_plan", String(64), index=True)
    plan_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    diagnostics: Mapped[list] = mapped_column("diagnosticos", JSONB, nullable=False, default=list)
    manifest: Mapped[dict] = mapped_column("manifiesto", JSONB, nullable=False, default=dict)
    artifact_path: Mapped[str | None] = mapped_column("ruta_artefacto", String(500))
    error_detail: Mapped[str | None] = mapped_column("detalle_error", Text)
