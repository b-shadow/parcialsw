from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base

if TYPE_CHECKING:
    from app.modules.proyectos_colaboracion.models.proyecto import Proyecto


class VersionProyecto(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "versiones_proyecto"
    __table_args__ = (
        UniqueConstraint("proyecto_id", "numero_version", name="uq_versiones_proyecto_proyecto_id_numero_version"),
        UniqueConstraint(
            "proyecto_id",
            "usuario_creador_id",
            "clave_idempotencia",
            name="uq_versiones_proyecto_proyecto_id_usuario_creador_id_c_380aa049",
        ),
        CheckConstraint("numero_version > 0", name="ck_versiones_proyecto_numero_version"),
        CheckConstraint("version_esquema_instantanea > 0", name="ck_versiones_proyecto_version_esquema_instantanea"),
        CheckConstraint(
            "almacenamiento_instantanea = 'mongodb'",
            name="ck_versiones_proyecto_almacenamiento_instantanea",
        ),
        CheckConstraint(
            "clase IN ('manual', 'pre_restore_backup')",
            name="ck_versiones_proyecto_clase",
        ),
        Index("ix_versiones_proyecto_proyecto_id_fecha_creacion", "proyecto_id", "fecha_creacion"),
        Index("ix_versiones_proyecto_fecha_creacion_id", "fecha_creacion", "id"),
    )

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id"), index=True
    )
    created_by_user_id: Mapped[UUID] = mapped_column("usuario_creador_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    version_number: Mapped[int] = mapped_column("numero_version", Integer, nullable=False)
    name: Mapped[str] = mapped_column("nombre", String(120), nullable=False)
    description: Mapped[str | None] = mapped_column("descripcion", Text)
    snapshot: Mapped[dict] = mapped_column("instantanea", JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column("estado", String(40), nullable=False, default="saved")
    kind: Mapped[str] = mapped_column("clase", String(40), nullable=False, default="manual", index=True)
    snapshot_schema_version: Mapped[int] = mapped_column("version_esquema_instantanea", Integer, nullable=False, default=2)
    snapshot_hash: Mapped[str] = mapped_column("hash_instantanea", String(64), nullable=False, default="")
    snapshot_size_bytes: Mapped[int] = mapped_column("tamano_instantanea_bytes", Integer, nullable=False, default=0)
    project_revision: Mapped[int] = mapped_column("revision_proyecto", Integer, nullable=False, default=0)
    idempotency_key: Mapped[str | None] = mapped_column("clave_idempotencia", String(120))
    metadata_json: Mapped[dict] = mapped_column("metadatos_json", JSONB, nullable=False, default=dict)
    snapshot_storage: Mapped[str] = mapped_column("almacenamiento_instantanea",
        String(20), nullable=False, default="mongodb", server_default="mongodb"
    )

    project: Mapped[Proyecto] = relationship(back_populates="versions")
