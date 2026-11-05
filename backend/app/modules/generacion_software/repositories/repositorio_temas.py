from datetime import datetime
from uuid import UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.generacion_software.models import ConfiguracionTemaFlutter, TemaFlutterPredefinido
from app.modules.proyectos_colaboracion.models import Proyecto


class RepositorioTemas:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, project_id: UUID) -> ConfiguracionTemaFlutter | None:
        project = self.db.get(Proyecto, project_id)
        if project is None:
            return None
        data = (project.settings or {}).get("flutter_theme")
        if not isinstance(data, dict):
            return None
        return ConfiguracionTemaFlutter(
            id=UUID(str(data["id"])) if data.get("id") else uuid5(project_id, "flutter-theme"),
            project_id=project_id,
            config_json=data["config_json"],
            preset_name=data.get("preset_name"),
            schema_version=data.get("schema_version", 2),
            revision=data.get("revision", 1),
            created_by_user_id=UUID(str(data.get("created_by_user_id", project.owner_id))),
            updated_by_user_id=UUID(str(data.get("updated_by_user_id", project.owner_id))),
            created_at=datetime.fromisoformat(data.get("created_at", project.created_at.isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", project.updated_at.isoformat())),
        )

    def listar_predefinidos(self, project_id: UUID) -> list[TemaFlutterPredefinido]:
        return list(self.db.scalars(select(TemaFlutterPredefinido).where(
            TemaFlutterPredefinido.project_id == project_id
        ).order_by(func.lower(TemaFlutterPredefinido.name))))

    def obtener_predefinido(self, preset_id: UUID) -> TemaFlutterPredefinido | None:
        return self.db.get(TemaFlutterPredefinido, preset_id)

    def agregar_predefinido(self, preset: TemaFlutterPredefinido) -> TemaFlutterPredefinido:
        self.db.add(preset)
        self.db.flush()
        self.db.refresh(preset)
        return preset
