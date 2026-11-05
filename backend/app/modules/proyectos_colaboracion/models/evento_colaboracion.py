from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


class EventoColaboracion(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "eventos_colaboracion"
    __table_args__ = (
        UniqueConstraint(
            "proyecto_id", "numero_secuencia", name="uq_eventos_colaboracion_proyecto_id_numero_secuencia"
        ),
        UniqueConstraint(
            "proyecto_id",
            "usuario_id",
            "evento_cliente_id",
            name="uq_eventos_colaboracion_proyecto_id_usuario_id_evento__06c6fc5f",
        ),
    )

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id"), index=True
    )
    diagram_id: Mapped[UUID | None] = mapped_column("diagrama_id", PG_UUID(as_uuid=True), ForeignKey("diagramas_uml.id"))
    user_id: Mapped[UUID] = mapped_column("usuario_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), index=True)
    client_event_id: Mapped[UUID] = mapped_column("evento_cliente_id", PG_UUID(as_uuid=True), nullable=False)
    sequence_number: Mapped[int] = mapped_column("numero_secuencia", Integer, nullable=False)
    event_type: Mapped[str] = mapped_column("tipo_evento", String(80), nullable=False, index=True)
    element_type: Mapped[str | None] = mapped_column("tipo_elemento", String(80))
    element_id: Mapped[UUID | None] = mapped_column("elemento_id", PG_UUID(as_uuid=True))
    base_version: Mapped[int | None] = mapped_column("version_base", Integer)
    payload: Mapped[dict] = mapped_column("carga_datos", JSONB, nullable=False, default=dict)
    actor_display_name: Mapped[str | None] = mapped_column("nombre_visible_actor", String(160))
    resource_type: Mapped[str | None] = mapped_column("tipo_recurso", String(80))
    resource_id: Mapped[UUID | None] = mapped_column("recurso_id", PG_UUID(as_uuid=True))
    correlation_id: Mapped[UUID | None] = mapped_column("correlacion_id", PG_UUID(as_uuid=True), index=True)
    causation_id: Mapped[UUID | None] = mapped_column("causa_id", PG_UUID(as_uuid=True))
    summary_key: Mapped[str | None] = mapped_column("clave_resumen", String(160))
