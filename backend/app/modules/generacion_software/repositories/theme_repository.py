from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.generacion_software.models import FlutterThemePreset, FlutterThemeSettings


class ThemeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, project_id: UUID) -> FlutterThemeSettings | None:
        return self.db.scalar(
            select(FlutterThemeSettings).where(
                FlutterThemeSettings.project_id == project_id
            )
        )

    def get_for_update(self, project_id: UUID) -> FlutterThemeSettings | None:
        return self.db.scalar(
            select(FlutterThemeSettings).where(
                FlutterThemeSettings.project_id == project_id
            ).with_for_update()
        )

    def add(self, theme: FlutterThemeSettings) -> FlutterThemeSettings:
        self.db.add(theme)
        self.db.flush()
        self.db.refresh(theme)
        return theme

    def list_presets(self, project_id: UUID) -> list[FlutterThemePreset]:
        return list(self.db.scalars(select(FlutterThemePreset).where(
            FlutterThemePreset.project_id == project_id
        ).order_by(func.lower(FlutterThemePreset.name))))

    def get_preset(self, preset_id: UUID) -> FlutterThemePreset | None:
        return self.db.get(FlutterThemePreset, preset_id)

    def add_preset(self, preset: FlutterThemePreset) -> FlutterThemePreset:
        self.db.add(preset)
        self.db.flush()
        self.db.refresh(preset)
        return preset

