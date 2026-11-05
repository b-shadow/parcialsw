from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.modules.asistente_proyecto.models import AccionIA
from app.modules.asistente_proyecto.repositories.repositorio_asistente import RepositorioAsistente
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente
from app.modules.modelado_uml.repositories.repositorio_uml import RepositorioUML
from app.modules.modelado_uml.schemas.especificacion_metodo import CreacionEspecificacionMetodoUML
from app.modules.modelado_uml.schemas.uml import (
    SolicitudActualizacionAtributoUML,
    SolicitudActualizacionClaseUML,
    SolicitudActualizacionMetodoUML,
    SolicitudActualizacionRelacionUML,
    SolicitudCreacionAtributoUML,
    SolicitudCreacionClaseUML,
    SolicitudCreacionMetodoUML,
    SolicitudCreacionRelacionUML,
)
from app.modules.modelado_uml.services.servicio_especificacion_metodo import (
    ServicioEspecificacionMetodo,
)
from app.modules.modelado_uml.services.servicio_uml import ServicioUML
from app.modules.proyectos_colaboracion.schemas.proyecto import SolicitudCreacionVersion
from app.modules.proyectos_colaboracion.services.servicio_proyectos import ServicioProyectos
from app.modules.proyectos_colaboracion.validators.validador_proyecto import (
    asegurar_permiso_proyecto,
)


class ServicioEjecucionAccionesIA:
    """Ejecuta solo el catalogo tipado; nunca interpreta codigo devuelto por IA."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = RepositorioAsistente(db)
        self.contracts = ServicioContratoAsistente(db)
        if settings.nosql_consolidated_mode:
            from app.modules.modelado_uml.repositories.repositorio_mongo_uml import (
                RepositorioMongoUML,
            )

            self.uml_repository = RepositorioMongoUML(db)
        else:
            self.uml_repository = RepositorioUML(db)
        self.uml = ServicioUML(db)

    def confirmar(self, project_id: UUID, action_id: UUID, user_id: UUID) -> tuple[AccionIA, bool]:
        asegurar_permiso_proyecto(self.db, project_id, user_id, "ai.confirm_actions")
        _project, _member = self.contracts._proyecto_y_miembro(project_id, user_id)
        action = self.repository.obtener_accion(project_id, action_id, for_update=True)
        if action is None:
            raise HTTPException(status_code=404, detail="Accion de IA no encontrada")
        if action.status == "applied":
            return action, True
        if action.status in {"rejected", "cancelled"}:
            raise HTTPException(status_code=409, detail="La accion ya no puede confirmarse")
        if action.status in {"confirmed", "executing"}:
            action.status = "failed"
            action.error_message = "Ejecucion anterior interrumpida; solicita una nueva propuesta"
            self.db.commit()
            raise HTTPException(status_code=409, detail=action.error_message)
        if action.status == "failed":
            raise HTTPException(status_code=409, detail="La accion fallo y requiere una nueva propuesta")
        self._verificar_dependencias(action)
        self._verificar_version_diagrama(action)
        action.status = "confirmed"
        action.confirmed_by_user_id = user_id
        action.confirmed_at = datetime.now(UTC)
        self.db.commit()
        action.status = "executing"
        self.db.commit()
        try:
            self.db.info["change_origin"] = "ai"
            try:
                result = self._ejecutar(action, user_id)
            finally:
                self.db.info.pop("change_origin", None)
            diagram_id = self._uuid((action.payload.get("_plan") or {}).get("diagram_id"))
            if diagram_id is not None and action.action_type not in {
                "prepare_backend_generation",
                "prepare_flutter_generation",
            }:
                validation = self.uml.validar_diagrama(diagram_id, user_id)
                result["validation"] = validation.model_dump(mode="json")
            action = self.repository.obtener_accion(project_id, action_id, for_update=True)
            action.status = "applied"
            action.executed_at = datetime.now(UTC)
            action.result_json = result
            action.error_message = None
            self.db.commit()
            self.db.refresh(action)
            return action, False
        except HTTPException as exc:
            self._marcar_fallida(project_id, action_id, str(exc.detail))
            raise
        except Exception as exc:
            self._marcar_fallida(project_id, action_id, "Fallo controlado al ejecutar la accion")
            raise HTTPException(status_code=422, detail="No se pudo aplicar la accion propuesta") from exc

    def rechazar(self, project_id: UUID, action_id: UUID, user_id: UUID) -> tuple[AccionIA, bool]:
        asegurar_permiso_proyecto(self.db, project_id, user_id, "ai.confirm_actions")
        action = self.repository.obtener_accion(project_id, action_id, for_update=True)
        if action is None:
            raise HTTPException(status_code=404, detail="Accion de IA no encontrada")
        if action.status == "rejected":
            return action, True
        if action.status != "proposed":
            raise HTTPException(status_code=409, detail="Solo se rechazan acciones propuestas")
        action.status = "rejected"
        self.db.commit()
        self.db.refresh(action)
        return action, False

    def _ejecutar(self, action: AccionIA, user_id: UUID) -> dict:
        payload = {key: value for key, value in action.payload.items() if key != "_plan"}
        plan = action.payload.get("_plan") or {}
        diagram_id = self._uuid(plan.get("diagram_id"))
        action_type = action.action_type
        if action_type == "create_class":
            item = self.uml.crear_clase(diagram_id, SolicitudCreacionClaseUML(**payload), user_id)
            return {"id": str(item.id), "type": "uml_class"}
        if action_type == "update_class":
            item = self.uml.actualizar_clase(self._destino_requerido(action), SolicitudActualizacionClaseUML(**payload), user_id)
            return {"id": str(item.id), "type": "uml_class"}
        if action_type == "delete_class":
            target = self._destino_requerido(action)
            self.uml.eliminar_clase(target, user_id)
            return {"id": str(target), "deleted": True}
        if action_type == "create_attribute":
            class_id = self._resolver_clase(diagram_id, payload)
            values = {key: value for key, value in payload.items() if key not in {"class_id", "class_name"}}
            item = self.uml.agregar_atributo(class_id, SolicitudCreacionAtributoUML(**values), user_id)
            return {"id": str(item.id), "type": "uml_attribute"}
        if action_type == "update_attribute":
            item = self.uml.actualizar_atributo(self._destino_requerido(action), SolicitudActualizacionAtributoUML(**payload), user_id)
            return {"id": str(item.id), "type": "uml_attribute"}
        if action_type == "delete_attribute":
            target = self._destino_requerido(action)
            self.uml.eliminar_atributo(target, user_id)
            return {"id": str(target), "deleted": True}
        if action_type == "create_method":
            class_id = self._resolver_clase(diagram_id, payload)
            values = {key: value for key, value in payload.items() if key not in {"class_id", "class_name", "data_type"}}
            item = self.uml.agregar_metodo(class_id, SolicitudCreacionMetodoUML(**values), user_id)
            return {"id": str(item.id), "type": "uml_method"}
        if action_type == "update_method":
            item = self.uml.actualizar_metodo(self._destino_requerido(action), SolicitudActualizacionMetodoUML(**payload), user_id)
            return {"id": str(item.id), "type": "uml_method"}
        if action_type == "delete_method":
            target = self._destino_requerido(action)
            self.uml.eliminar_metodo(target, user_id)
            return {"id": str(target), "deleted": True}
        if action_type == "create_relationship":
            values = dict(payload)
            values["source_class_id"] = self._resolver_clase_por_nombre(
                diagram_id, values.pop("source_class_id", None), values.pop("source_class_name", None)
            )
            values["target_class_id"] = self._resolver_clase_por_nombre(
                diagram_id, values.pop("target_class_id", None), values.pop("target_class_name", None)
            )
            item = self.uml.crear_relacion(
                diagram_id, SolicitudCreacionRelacionUML(**values), user_id
            )
            return {"id": str(item.id), "type": "uml_relationship"}
        if action_type == "update_relationship":
            item = self.uml.actualizar_relacion(
                self._destino_requerido(action), SolicitudActualizacionRelacionUML(**payload), user_id
            )
            return {"id": str(item.id), "type": "uml_relationship"}
        if action_type == "delete_relationship":
            target = self._destino_requerido(action)
            self.uml.eliminar_relacion(target, user_id)
            return {"id": str(target), "deleted": True}
        if action_type == "update_method_specification":
            plan = action.payload.get("_plan") or {}
            expected_revision = int(plan.get("base_spec_revision", 0))
            item = ServicioEspecificacionMetodo(self.db).put(
                self._destino_requerido(action),
                CreacionEspecificacionMetodoUML(**payload),
                user_id,
                expected_revision=expected_revision,
                create_only=expected_revision == 0,
                commit=False,
            )
            method = self.uml_repository.obtener_metodo(item.method_id)
            return {
                "id": str(item.id),
                "type": "uml_method_specification",
                "method_id": str(item.method_id),
                "class_id": str(method.class_id) if method else None,
                "revision": item.revision,
                "created": expected_revision == 0,
            }
        if action_type == "save_version":
            item = ServicioProyectos(self.db).crear_version(
                action.project_id,
                SolicitudCreacionVersion(
                    name=str(payload.get("name") or "Version guardada por IA"),
                    description=payload.get("description"),
                ),
                user_id,
            )
            return {"id": str(item.id), "version_number": item.version_number}
        if action_type in {"prepare_backend_generation", "prepare_flutter_generation"}:
            return {
                "prepared": True,
                "target": "backend" if action_type == "prepare_backend_generation" else "flutter",
                "diagram_id": str(diagram_id) if diagram_id else None,
            }
        raise HTTPException(status_code=422, detail="Tipo de accion no soportado")

    def _verificar_dependencias(self, action: AccionIA) -> None:
        plan = action.payload.get("_plan") or {}
        for raw_key in plan.get("depends_on") or []:
            dependency = self.repository.obtener_accion_por_idempotencia(
                action.project_id, self._uuid(raw_key)
            )
            if dependency is None or dependency.status != "applied":
                raise HTTPException(status_code=409, detail="Primero confirma las acciones dependientes")

    def _verificar_version_diagrama(self, action: AccionIA) -> None:
        plan = action.payload.get("_plan") or {}
        diagram_id = self._uuid(plan.get("diagram_id"))
        expected = plan.get("base_diagram_version")
        if diagram_id is None or expected is None:
            return
        diagram = self.uml_repository.obtener_diagrama(diagram_id)
        if diagram is None or diagram.project_id != action.project_id:
            raise HTTPException(status_code=404, detail="Diagrama de la accion no encontrado")
        if diagram.current_version != expected and not plan.get("depends_on"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El diagrama cambio; solicita a la IA un plan actualizado",
            )

    def _resolver_clase(self, diagram_id: UUID | None, payload: dict) -> UUID:
        return self._resolver_clase_por_nombre(
            diagram_id, payload.get("class_id"), payload.get("class_name")
        )

    def _resolver_clase_por_nombre(
        self, diagram_id: UUID | None, raw_id: object, name: object
    ) -> UUID:
        class_id = self._uuid(raw_id)
        if class_id:
            item = self.uml_repository.obtener_clase(class_id)
            if item is not None and (diagram_id is None or item.diagram_id == diagram_id):
                return class_id
        if diagram_id and name:
            for item in self.uml_repository.listar_clases(diagram_id):
                if item.name.casefold() == str(name).casefold():
                    return item.id
        raise HTTPException(status_code=422, detail="No se pudo resolver la clase objetivo")

    @staticmethod
    def _destino_requerido(action: AccionIA) -> UUID:
        if action.target_id is None:
            raise HTTPException(status_code=422, detail="La accion no identifica su objetivo")
        return action.target_id

    @staticmethod
    def _uuid(value: object) -> UUID | None:
        if value is None:
            return None
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None

    def _marcar_fallida(self, project_id: UUID, action_id: UUID, message: str) -> None:
        self.db.rollback()
        action = self.repository.obtener_accion(project_id, action_id, for_update=True)
        if action is not None:
            action.status = "failed"
            action.error_message = message[:2000]
            self.db.commit()
