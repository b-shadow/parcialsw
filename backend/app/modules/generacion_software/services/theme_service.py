from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.generacion_software.models import FlutterThemePreset, FlutterThemeSettings
from app.modules.generacion_software.repositories.theme_repository import ThemeRepository
from app.modules.generacion_software.schemas.theme import (
    FlutterThemePresetResponse,
    FlutterThemePresetWrite,
    FlutterThemeResponse,
    FlutterThemeUpdate,
    FlutterThemeValidationResponse,
)
from app.modules.generacion_software.schemas.theme_contract import (
    DEFAULT_THEME_V2,
    SYSTEM_THEME_PRESETS,
    normalize_theme,
)
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.repositories.project_repository import ProjectRepository
from app.modules.proyectos_colaboracion.services.project_mutation_guard import ProjectMutationGuard
from app.modules.proyectos_colaboracion.validators.project_validator import (
    ensure_membership,
    ensure_project_exists,
    ensure_project_permission,
)


class ThemeService:
    MAX_CUSTOM_PRESETS = 20

    def __init__(self, db: Session) -> None:
        self.db = db
        self.themes = ThemeRepository(db)
        self.members = MemberRepository(db)
        self.projects = ProjectRepository(db)
        self.audit = AuditService(db)
        self.mutations = ProjectMutationGuard(db)

    def get(self, project_id: UUID, user_id: UUID) -> FlutterThemeResponse:
        self._require_member(project_id, user_id)
        theme = self.themes.get(project_id)
        if theme is None:
            return self._default_response(project_id)
        return self._response(theme)

    def validate(self, project_id: UUID, config: dict, user_id: UUID) -> FlutterThemeValidationResponse:
        self._require_member(project_id, user_id)
        theme, diagnostics, fields = normalize_theme(config)
        return FlutterThemeValidationResponse(
            theme=theme, diagnostics=diagnostics, normalized_fields=fields,
            valid=not any(item.severity == "error" for item in diagnostics),
        )

    def put(self, project_id: UUID, payload: FlutterThemeUpdate, user_id: UUID, expected_revision: int | None) -> FlutterThemeResponse:
        self._require_editor(project_id, user_id)
        project = self.mutations.acquire(project_id)
        normalized = self.validate(project_id, payload.config, user_id)
        self._reject_invalid(normalized)
        theme = self.themes.get_for_update(project_id)
        self._check_revision(theme, expected_revision)
        values = normalized.theme.model_dump(mode="json")
        changed = False
        if theme is None:
            theme = self.themes.add(FlutterThemeSettings(
                project_id=project_id, config_json=values, preset_name=payload.preset_name,
                schema_version=2, revision=1, created_by_user_id=user_id, updated_by_user_id=user_id,
            ))
            changed = True
        elif theme.config_json != values or theme.preset_name != payload.preset_name:
            theme.config_json = values
            theme.preset_name = payload.preset_name
            theme.schema_version = 2
            theme.revision += 1
            theme.updated_by_user_id = user_id
            changed = True
        if changed:
            self.mutations.advance(project)
            self.audit.record(module="generacion_software", action="FLUTTER_THEME_UPDATED",
                              user_id=user_id, project_id=project_id,
                              metadata={"revision": theme.revision, "normalized_fields": normalized.normalized_fields})
            try:
                self.db.commit()
                self.db.refresh(theme)
            except IntegrityError as exc:
                self.db.rollback()
                raise HTTPException(status_code=409, detail={
                    "code": "flutter_theme_revision_conflict",
                    "message": "El tema fue creado o modificado en otra sesion.",
                }) from exc
            return self._response(theme)
        response = self._response(theme)
        self.db.rollback()
        return response

    def reset(self, project_id: UUID, user_id: UUID, expected_revision: int | None) -> FlutterThemeResponse:
        return self.put(project_id, FlutterThemeUpdate(config=DEFAULT_THEME_V2.model_dump(mode="json")), user_id, expected_revision)

    def list_presets(self, project_id: UUID, user_id: UUID) -> list[FlutterThemePresetResponse]:
        self._require_member(project_id, user_id)
        system = [FlutterThemePresetResponse(id=item["id"], kind="system", name=item["name"],
                  description=item["description"], config=item["config"]) for item in SYSTEM_THEME_PRESETS]
        custom = [self._preset_response(item) for item in self.themes.list_presets(project_id)]
        return [*system, *custom]

    def create_preset(self, project_id: UUID, payload: FlutterThemePresetWrite, user_id: UUID) -> FlutterThemePresetResponse:
        self._require_editor(project_id, user_id)
        if len(self.themes.list_presets(project_id)) >= self.MAX_CUSTOM_PRESETS:
            raise HTTPException(status_code=422, detail="Limite de presets personalizados alcanzado")
        normalized = self.validate(project_id, payload.config, user_id)
        self._reject_invalid(normalized)
        try:
            preset = self.themes.add_preset(FlutterThemePreset(
                project_id=project_id, name=payload.name.strip(),
                config_json=normalized.theme.model_dump(mode="json"), schema_version=2,
                created_by_user_id=user_id, updated_by_user_id=user_id,
            ))
            self.audit.record(module="generacion_software", action="FLUTTER_THEME_PRESET_CREATED",
                              user_id=user_id, project_id=project_id, metadata={"preset_id": str(preset.id)})
            self.db.commit()
            self.db.refresh(preset)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Ya existe un preset con ese nombre") from exc
        return self._preset_response(preset)

    def update_preset(self, project_id: UUID, preset_id: UUID, payload: FlutterThemePresetWrite, user_id: UUID) -> FlutterThemePresetResponse:
        self._require_editor(project_id, user_id)
        preset = self._owned_preset(project_id, preset_id)
        normalized = self.validate(project_id, payload.config, user_id)
        self._reject_invalid(normalized)
        preset.name = payload.name.strip()
        preset.config_json = normalized.theme.model_dump(mode="json")
        preset.schema_version = 2
        preset.updated_by_user_id = user_id
        try:
            self.audit.record(module="generacion_software", action="FLUTTER_THEME_PRESET_UPDATED",
                              user_id=user_id, project_id=project_id, metadata={"preset_id": str(preset.id)})
            self.db.commit()
            self.db.refresh(preset)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="Ya existe un preset con ese nombre") from exc
        return self._preset_response(preset)

    def delete_preset(self, project_id: UUID, preset_id: UUID, user_id: UUID) -> None:
        self._require_editor(project_id, user_id)
        self.db.delete(self._owned_preset(project_id, preset_id))
        self.audit.record(module="generacion_software", action="FLUTTER_THEME_PRESET_DELETED",
                          user_id=user_id, project_id=project_id, metadata={"preset_id": str(preset_id)})
        self.db.commit()

    def apply_preset(self, project_id: UUID, preset_id: str, user_id: UUID, expected_revision: int) -> FlutterThemeResponse:
        self._require_editor(project_id, user_id)
        system = next((item for item in SYSTEM_THEME_PRESETS if item["id"] == preset_id), None)
        if system:
            return self.put(project_id, FlutterThemeUpdate(config=system["config"], preset_name=system["name"]), user_id, expected_revision)
        try:
            custom = self._owned_preset(project_id, UUID(preset_id))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Preset no encontrado") from exc
        return self.put(project_id, FlutterThemeUpdate(config=custom.config_json, preset_name=custom.name), user_id, expected_revision)

    def _require_member(self, project_id: UUID, user_id: UUID):
        ensure_project_exists(self.projects.get(project_id))
        return ensure_membership(self.members.get_membership(project_id, user_id))

    def _require_editor(self, project_id: UUID, user_id: UUID):
        ensure_project_exists(self.projects.get(project_id))
        return ensure_project_permission(self.db, project_id, user_id, "theme.edit")

    @staticmethod
    def _check_revision(theme: FlutterThemeSettings | None, expected: int | None) -> None:
        current = theme.revision if theme else 0
        required = 0 if theme is None else current
        if expected is None or expected != required:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "code": "flutter_theme_revision_conflict", "current_revision": current,
                "message": "El tema cambio en otra sesion; recargue o reaplique su borrador.",
            })

    @staticmethod
    def _reject_invalid(result: FlutterThemeValidationResponse) -> None:
        if not result.valid:
            raise HTTPException(status_code=422, detail={"code": "invalid_flutter_theme",
                "diagnostics": [item.model_dump(mode="json") for item in result.diagnostics]})

    def _owned_preset(self, project_id: UUID, preset_id: UUID) -> FlutterThemePreset:
        preset = self.themes.get_preset(preset_id)
        if preset is None or preset.project_id != project_id:
            raise HTTPException(status_code=404, detail="Preset no encontrado")
        return preset

    @staticmethod
    def _default_response(project_id: UUID) -> FlutterThemeResponse:
        return FlutterThemeResponse(id=None, project_id=project_id, theme=DEFAULT_THEME_V2,
            preset_name=None, revision=0, created_by_user_id=None, updated_by_user_id=None,
            created_at=None, updated_at=None, diagnostics=[], normalized_fields=[], valid=True)

    @staticmethod
    def _response(theme: FlutterThemeSettings) -> FlutterThemeResponse:
        config, diagnostics, fields = normalize_theme(theme.config_json)
        return FlutterThemeResponse(id=theme.id, project_id=theme.project_id, theme=config,
            preset_name=theme.preset_name, revision=theme.revision,
            created_by_user_id=theme.created_by_user_id, updated_by_user_id=theme.updated_by_user_id,
            created_at=theme.created_at, updated_at=theme.updated_at,
            diagnostics=diagnostics, normalized_fields=fields,
            valid=not any(item.severity == "error" for item in diagnostics))

    @staticmethod
    def _preset_response(preset: FlutterThemePreset) -> FlutterThemePresetResponse:
        config, _, _ = normalize_theme(preset.config_json)
        return FlutterThemePresetResponse(id=str(preset.id), kind="custom", name=preset.name,
            config=config, updated_at=preset.updated_at)
