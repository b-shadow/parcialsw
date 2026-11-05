from datetime import UTC, datetime
from uuid import UUID, uuid5

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.services.servicio_auditoria import ServicioAuditoria
from app.modules.generacion_software.models import ConfiguracionTemaFlutter, TemaFlutterPredefinido
from app.modules.generacion_software.repositories.repositorio_temas import RepositorioTemas
from app.modules.generacion_software.schemas.contrato_temas import (
    DEFAULT_THEME_V2,
    SYSTEM_THEME_PRESETS,
    normalizar_tema,
)
from app.modules.generacion_software.schemas.temas import (
    ActualizacionTemaFlutter,
    EscrituraTemaFlutterPredefinido,
    RespuestaTemaFlutter,
    RespuestaTemaFlutterPredefinido,
    RespuestaValidacionTemaFlutter,
)
from app.modules.proyectos_colaboracion.repositories.repositorio_integrantes import (
    RepositorioIntegrantes,
)
from app.modules.proyectos_colaboracion.repositories.repositorio_proyectos import (
    RepositorioProyectos,
)
from app.modules.proyectos_colaboracion.services.guardia_mutaciones_proyecto import (
    GuardiaMutacionesProyecto,
)
from app.modules.proyectos_colaboracion.validators.validador_proyecto import (
    asegurar_participacion,
    asegurar_permiso_proyecto,
    asegurar_proyecto_existente,
)


class ServicioTemas:
    MAX_CUSTOM_PRESETS = 20

    def __init__(self, db: Session) -> None:
        self.db = db
        self.themes = RepositorioTemas(db)
        self.members = RepositorioIntegrantes(db)
        self.projects = RepositorioProyectos(db)
        self.audit = ServicioAuditoria(db)
        self.mutations = GuardiaMutacionesProyecto(db)

    def get(self, project_id: UUID, user_id: UUID) -> RespuestaTemaFlutter:
        self._require_member(project_id, user_id)
        theme = self.themes.get(project_id)
        if theme is None:
            return self._respuesta_predeterminada(project_id)
        return self._response(theme)

    def validate(self, project_id: UUID, config: dict, user_id: UUID) -> RespuestaValidacionTemaFlutter:
        self._require_member(project_id, user_id)
        theme, diagnostics, fields = normalizar_tema(config)
        return RespuestaValidacionTemaFlutter(
            theme=theme, diagnostics=diagnostics, normalized_fields=fields,
            valid=not any(item.severity == "error" for item in diagnostics),
        )

    def put(self, project_id: UUID, payload: ActualizacionTemaFlutter, user_id: UUID, expected_revision: int | None) -> RespuestaTemaFlutter:
        self._requerir_editor(project_id, user_id)
        project = self.mutations.acquire(project_id)
        normalized = self.validate(project_id, payload.config, user_id)
        self._rechazar_invalido(normalized)
        theme = self.themes.get(project_id)
        self._comprobar_revision(theme, expected_revision)
        values = normalized.theme.model_dump(mode="json")
        changed = theme is None or theme.config_json != values or theme.preset_name != payload.preset_name
        if changed:
            old = (project.settings or {}).get("flutter_theme", {})
            now = datetime.now(UTC).isoformat()
            revision = (theme.revision + 1) if theme else 1
            project.settings = {
                **(project.settings or {}),
                "flutter_theme": {
                    "id": old.get("id", str(uuid5(project_id, "flutter-theme"))),
                    "config_json": values,
                    "preset_name": payload.preset_name,
                    "schema_version": 2,
                    "revision": revision,
                    "created_by_user_id": old.get("created_by_user_id", str(user_id)),
                    "updated_by_user_id": str(user_id),
                    "created_at": old.get("created_at", now),
                    "updated_at": now,
                },
            }
            self.mutations.avanzar(project)
            self.audit.record(module="generacion_software", action="FLUTTER_THEME_UPDATED",
                              user_id=user_id, project_id=project_id,
                              metadata={"revision": revision, "normalized_fields": normalized.normalized_fields})
            try:
                self.db.commit()
            except IntegrityError as exc:
                self.db.rollback()
                raise HTTPException(status_code=409, detail={
                    "code": "flutter_theme_revision_conflict",
                    "message": "El tema fue creado o modificado en otra sesion.",
                }) from exc
            return self._response(self.themes.get(project_id))
        response = self._response(theme)
        self.db.rollback()
        return response

    def reset(self, project_id: UUID, user_id: UUID, expected_revision: int | None) -> RespuestaTemaFlutter:
        return self.put(project_id, ActualizacionTemaFlutter(config=DEFAULT_THEME_V2.model_dump(mode="json")), user_id, expected_revision)

    def listar_predefinidos(self, project_id: UUID, user_id: UUID) -> list[RespuestaTemaFlutterPredefinido]:
        self._require_member(project_id, user_id)
        system = [RespuestaTemaFlutterPredefinido(id=item["id"], kind="system", name=item["name"],
                  description=item["description"], config=item["config"]) for item in SYSTEM_THEME_PRESETS]
        custom = [self._respuesta_predefinido(item) for item in self.themes.listar_predefinidos(project_id)]
        return [*system, *custom]

    def crear_predefinido(self, project_id: UUID, payload: EscrituraTemaFlutterPredefinido, user_id: UUID) -> RespuestaTemaFlutterPredefinido:
        self._requerir_editor(project_id, user_id)
        if len(self.themes.listar_predefinidos(project_id)) >= self.MAX_CUSTOM_PRESETS:
            raise HTTPException(status_code=422, detail="Limite de presets personalizados alcanzado")
        normalized = self.validate(project_id, payload.config, user_id)
        self._rechazar_invalido(normalized)
        try:
            preset = self.themes.agregar_predefinido(TemaFlutterPredefinido(
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
        return self._respuesta_predefinido(preset)

    def actualizar_predefinido(self, project_id: UUID, preset_id: UUID, payload: EscrituraTemaFlutterPredefinido, user_id: UUID) -> RespuestaTemaFlutterPredefinido:
        self._requerir_editor(project_id, user_id)
        preset = self._predefinido_propio(project_id, preset_id)
        normalized = self.validate(project_id, payload.config, user_id)
        self._rechazar_invalido(normalized)
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
        return self._respuesta_predefinido(preset)

    def eliminar_predefinido(self, project_id: UUID, preset_id: UUID, user_id: UUID) -> None:
        self._requerir_editor(project_id, user_id)
        self.db.delete(self._predefinido_propio(project_id, preset_id))
        self.audit.record(module="generacion_software", action="FLUTTER_THEME_PRESET_DELETED",
                          user_id=user_id, project_id=project_id, metadata={"preset_id": str(preset_id)})
        self.db.commit()

    def aplicar_predefinido(self, project_id: UUID, preset_id: str, user_id: UUID, expected_revision: int) -> RespuestaTemaFlutter:
        self._requerir_editor(project_id, user_id)
        system = next((item for item in SYSTEM_THEME_PRESETS if item["id"] == preset_id), None)
        if system:
            return self.put(project_id, ActualizacionTemaFlutter(config=system["config"], preset_name=system["name"]), user_id, expected_revision)
        try:
            custom = self._predefinido_propio(project_id, UUID(preset_id))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Preset no encontrado") from exc
        return self.put(project_id, ActualizacionTemaFlutter(config=custom.config_json, preset_name=custom.name), user_id, expected_revision)

    def _require_member(self, project_id: UUID, user_id: UUID):
        asegurar_proyecto_existente(self.projects.get(project_id))
        return asegurar_participacion(self.members.obtener_participacion(project_id, user_id))

    def _requerir_editor(self, project_id: UUID, user_id: UUID):
        asegurar_proyecto_existente(self.projects.get(project_id))
        return asegurar_permiso_proyecto(self.db, project_id, user_id, "theme.edit")

    @staticmethod
    def _comprobar_revision(theme: ConfiguracionTemaFlutter | None, expected: int | None) -> None:
        current = theme.revision if theme else 0
        required = 0 if theme is None else current
        if expected is None or expected != required:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "code": "flutter_theme_revision_conflict", "current_revision": current,
                "message": "El tema cambio en otra sesion; recargue o reaplique su borrador.",
            })

    @staticmethod
    def _rechazar_invalido(result: RespuestaValidacionTemaFlutter) -> None:
        if not result.valid:
            raise HTTPException(status_code=422, detail={"code": "invalid_flutter_theme",
                "diagnostics": [item.model_dump(mode="json") for item in result.diagnostics]})

    def _predefinido_propio(self, project_id: UUID, preset_id: UUID) -> TemaFlutterPredefinido:
        preset = self.themes.obtener_predefinido(preset_id)
        if preset is None or preset.project_id != project_id:
            raise HTTPException(status_code=404, detail="Preset no encontrado")
        return preset

    @staticmethod
    def _respuesta_predeterminada(project_id: UUID) -> RespuestaTemaFlutter:
        return RespuestaTemaFlutter(id=None, project_id=project_id, theme=DEFAULT_THEME_V2,
            preset_name=None, revision=0, created_by_user_id=None, updated_by_user_id=None,
            created_at=None, updated_at=None, diagnostics=[], normalized_fields=[], valid=True)

    @staticmethod
    def _response(theme: ConfiguracionTemaFlutter) -> RespuestaTemaFlutter:
        config, diagnostics, fields = normalizar_tema(theme.config_json)
        return RespuestaTemaFlutter(id=theme.id, project_id=theme.project_id, theme=config,
            preset_name=theme.preset_name, revision=theme.revision,
            created_by_user_id=theme.created_by_user_id, updated_by_user_id=theme.updated_by_user_id,
            created_at=theme.created_at, updated_at=theme.updated_at,
            diagnostics=diagnostics, normalized_fields=fields,
            valid=not any(item.severity == "error" for item in diagnostics))

    @staticmethod
    def _respuesta_predefinido(preset: TemaFlutterPredefinido) -> RespuestaTemaFlutterPredefinido:
        config, _, _ = normalizar_tema(preset.config_json)
        return RespuestaTemaFlutterPredefinido(id=str(preset.id), kind="custom", name=preset.name,
            config=config, updated_at=preset.updated_at)
