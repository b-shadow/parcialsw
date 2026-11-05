from uuid import UUID

from ai_engine.context import (
    ContextoActor,
    ContextoDiagrama,
    ContextoIAProyecto,
    ContextoMensajeReciente,
    ContextoProyecto,
    ElementoActividadEquipo,
    RestriccionesContexto,
)
from ai_engine.context.presupuesto import PresupuestoContexto
from ai_engine.context.saneador import sanear_texto_no_confiable
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import Usuario
from app.modules.asistente_proyecto.models import ConfiguracionIAProyecto, ConversacionIA
from app.modules.asistente_proyecto.repositories.repositorio_asistente import RepositorioAsistente
from app.modules.asistente_proyecto.schemas.esquemas_asistente import ContextoSolicitado
from app.modules.asistente_proyecto.services.almacen_documentos_conversacion import (
    AlmacenDocumentosConversacion,
)
from app.modules.modelado_uml.repositories.repositorio_uml import RepositorioUML
from app.modules.modelado_uml.services.servicio_uml import ServicioUML
from app.modules.proyectos_colaboracion.models import IntegranteProyecto, Proyecto, VersionProyecto
from app.modules.proyectos_colaboracion.permisos import permisos_efectivos


class ConstructorContextoProyecto:
    """Construye exclusivamente contexto perteneciente al proyecto autorizado."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.assistant = RepositorioAsistente(db)
        self.uml = RepositorioUML(db)
        self.documents = AlmacenDocumentosConversacion()

    async def construir(
        self,
        *,
        project: Proyecto,
        member: IntegranteProyecto,
        user_id: UUID,
        conversation: ConversacionIA,
        settings: ConfiguracionIAProyecto,
        diagram_id: UUID | None,
        requested: ContextoSolicitado,
    ) -> ContextoIAProyecto:
        user = self.db.get(Usuario, user_id)
        permissions = sorted(permisos_efectivos(member.project_role))
        diagram_context = None
        if requested.include_diagram and diagram_id is not None:
            diagram = self.uml.obtener_diagrama(diagram_id)
            if diagram is None or diagram.project_id != project.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Diagrama no encontrado en el proyecto",
                )
            model = ServicioUML(self.db)._construir_modelo_interno(diagram)
            diagram_context = ContextoDiagrama(
                id=diagram.id,
                name=model.name,
                current_version=model.current_version,
                classes=[self._serializar_clase(item) for item in model.classes],
                relationships=[
                    {
                        "id": str(item.id),
                        "source_class_id": str(item.source_class_id),
                        "target_class_id": str(item.target_class_id),
                        "relationship_type": item.relationship_type,
                        "source_cardinality": item.source_cardinality,
                        "target_cardinality": item.target_cardinality,
                        "direction": item.direction,
                        "label": item.label,
                        "metadata_json": item.metadata_json,
                    }
                    for item in model.relationships
                ],
            )
        recent_messages: list[ContextoMensajeReciente] = []
        if requested.include_recent_messages:
            messages = await self._mensajes(conversation.id, settings.max_context_messages)
            author_ids = {item.author_user_id for item in messages if item.author_user_id}
            names_by_user = self.assistant.nombres_visibles_usuarios(author_ids) if author_ids else {}
            recent_messages = [
                ContextoMensajeReciente(
                    sequence_number=item.sequence_number,
                    role=item.role,
                    content=item.content,
                    author_display_name=names_by_user.get(item.author_user_id) if item.author_user_id else None,
                )
                for item in messages
            ]
        versions: list[dict] = []
        if requested.include_project_versions:
            records = self.db.scalars(
                select(VersionProyecto)
                .where(VersionProyecto.project_id == project.id)
                .order_by(VersionProyecto.version_number.desc())
                .limit(20)
            )
            versions = [
                {
                    "id": str(item.id),
                    "number": item.version_number,
                    "name": item.name,
                    "status": item.status,
                }
                for item in records
            ]
        pending_actions = self.assistant.listar_acciones(project.id, "proposed", 50)
        pending_recommendations = self.assistant.listar_recomendaciones(project.id, "open", None, 50)
        generation_state = {
            "pending_actions": [
                {
                    "id": str(item.id),
                    "action_type": item.action_type,
                    "target_type": item.target_type,
                    "target_id": str(item.target_id) if item.target_id else None,
                    "risk_level": item.risk_level,
                }
                for item in pending_actions
            ],
            "pending_recommendations": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "description": item.description,
                    "category": item.category,
                    "severity": item.severity,
                    "references": item.references_json,
                }
                for item in pending_recommendations
            ],
        }
        team_activity: list[ElementoActividadEquipo] = []
        try:
            from app.core.changelog.servicio import ServicioRegistroCambios
            cl_service = ServicioRegistroCambios()
            cl_page = cl_service.listar_proyecto(project.id, db=self.db, limit=50)
            cl_page = cl_service.resolver_nombres(self.db, cl_page)

            grouped: dict[str, dict] = {}
            for entry in cl_page.items:
                key = str(entry.actor_user_id) if entry.actor_user_id else (entry.actor_display_name or "sistema")
                name = entry.actor_display_name or ("Sistema" if not entry.actor_user_id else str(entry.actor_user_id))
                action_text = entry.summary or f"{entry.action} {entry.entity_type or ''}".strip()
                if not action_text:
                    continue
                if key not in grouped:
                    grouped[key] = {
                        "user_id": entry.actor_user_id,
                        "display_name": name,
                        "actions": [],
                        "last_at": entry.occurred_at,
                    }
                actor_data = grouped[key]
                if len(actor_data["actions"]) < 10 and action_text not in actor_data["actions"]:
                    actor_data["actions"].append(action_text)
                actor_data["last_at"] = max(actor_data["last_at"], entry.occurred_at)

            for data in grouped.values():
                team_activity.append(
                    ElementoActividadEquipo(
                        user_id=data["user_id"],
                        display_name=data["display_name"],
                        actions=data["actions"],
                        last_at=data["last_at"],
                    )
                )
        except Exception:
            team_activity = []

        context = ContextoIAProyecto(
            project=ContextoProyecto(
                id=project.id,
                name=project.name,
                description=project.description,
            ),
            actor=ContextoActor(
                id=user_id,
                display_name=user.full_name if user else "Usuario",
                project_role=member.project_role,
                permissions=permissions,
            ),
            active_diagram=diagram_context,
            recent_messages=recent_messages,
            conversation_summary=await self._memoria_conversaciones_proyecto(project.id, conversation),
            available_versions=versions,
            generation_state=generation_state,
            team_activity=team_activity,
            constraints=RestriccionesContexto(
                language="es",
                offline=True,
                require_confirmation=settings.require_confirmation,
                surface=requested.surface,
            ),
        )
        return PresupuestoContexto(max_chars=50000).aplicar(context).context

    async def _memoria_conversaciones_proyecto(
        self, project_id: UUID, current: ConversacionIA
    ) -> str | None:
        sections: list[str] = []
        for conversation in self.assistant.listar_conversaciones(project_id):
            snapshot = await self.documents.obtener_contexto_reciente_seguro(conversation.id)
            if snapshot is not None:
                memory = snapshot.summary
            elif conversation.summary:
                memory = conversation.summary
            elif conversation.id != current.id:
                messages = await self._mensajes(conversation.id, 20)
                memory = "\n".join(
                    f"{item.role}: {sanear_texto_no_confiable(item.content, 600)}"
                    for item in messages
                    if item.status == "completed"
                )
            else:
                memory = ""
            if not memory:
                continue
            scope = "chat actual" if conversation.id == current.id else "chat anterior"
            sections.append(f"[{scope}: {conversation.title}]\n{memory}")
        if not sections:
            return None
        joined = "\n\n".join(sections)
        return joined[-10000:]

    async def _mensajes(self, conversation_id: UUID, limit: int):
        sql_items = self.assistant.listar_mensajes(
            conversation_id,
            before_sequence=None,
            after_sequence=None,
            limit=limit,
        )
        mongo_items = await self.documents.listar_mensajes_seguro(
            conversation_id,
            before_sequence=None,
            after_sequence=None,
            limit=limit,
        )
        if mongo_items is None:
            return sql_items
        by_sequence = {item.sequence_number: item for item in mongo_items}
        for item in sql_items:
            by_sequence.setdefault(item.sequence_number, item)
        return sorted(by_sequence.values(), key=lambda item: item.sequence_number)[-limit:]

    @staticmethod
    def _serializar_clase(item) -> dict:
        return {
            "id": str(item.id),
            "name": item.name,
            "element_type": item.element_type,
            "stereotype": item.stereotype,
            "attributes": [
                {
                    "id": str(attribute.id),
                    "name": attribute.name,
                    "data_type": attribute.data_type,
                    "multiplicity": attribute.multiplicity,
                    "required": attribute.is_required,
                }
                for attribute in item.attributes
            ],
            "methods": [
                {
                    "id": str(method.id),
                    "name": method.name,
                    "return_type": method.return_type,
                    "parameters": [
                        {
                            "id": str(parameter.id),
                            "name": parameter.name,
                            "data_type": parameter.data_type,
                        }
                        for parameter in method.parameters
                    ],
                }
                for method in item.methods
            ],
        }
