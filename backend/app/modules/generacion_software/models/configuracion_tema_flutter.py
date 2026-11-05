from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.componentes_modelo import ComponenteClavePrimariaUUID, ComponenteMarcasTiempo
from app.core.database.sesion import Base


@dataclass
class ConfiguracionTemaFlutter:
    """Vista del tema activo guardado en projects.settings.flutter_theme."""

    id: UUID
    project_id: UUID
    config_json: dict
    preset_name: str | None
    schema_version: int
    revision: int
    created_by_user_id: UUID
    updated_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class TemaFlutterPredefinido(ComponenteClavePrimariaUUID, ComponenteMarcasTiempo, Base):
    __tablename__ = "temas_flutter_predefinidos"
    __table_args__ = (
        Index("ix_temas_flutter_predefinidos_proyecto_id_2", "proyecto_id", text("lower(nombre)"), unique=True),
        CheckConstraint("version_esquema > 0", name="ck_temas_flutter_predefinidos_version_esquema"),
    )

    project_id: Mapped[UUID] = mapped_column("proyecto_id",
        PG_UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column("nombre", String(120), nullable=False)
    config_json: Mapped[dict] = mapped_column("configuracion_json", JSONB, nullable=False, default=dict)
    schema_version: Mapped[int] = mapped_column("version_esquema", Integer, nullable=False, default=2)
    created_by_user_id: Mapped[UUID] = mapped_column("usuario_creador_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    updated_by_user_id: Mapped[UUID] = mapped_column("usuario_actualizador_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
