from uuid import UUID

from ai_engine.context import (
    ActorContext,
    AiProjectContext,
    ContextConstraints,
    DiagramContext,
    ProjectContext,
    RecentMessageContext,
)
from ai_engine.context.sanitizer import sanitize_untrusted_text
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import User
from app.modules.asistente_proyecto.models import AiConversation, AiProjectSettings
from app.modules.asistente_proyecto.repositories.assistant_repository import AssistantRepository
from app.modules.asistente_proyecto.schemas.assistant import RequestedContext
from app.modules.modelado_uml.repositories.uml_repository import UmlRepository
from app.modules.proyectos_colaboracion.models import Project, ProjectMember, ProjectVersion


class ProjectContextBuilder:
    """Construye exclusivamente contexto perteneciente al proyecto autorizado."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.assistant = AssistantRepository(db)
        self.uml = UmlRepository(db)

    def build(
        self,
        *,
        project: Project,
        member: ProjectMember,
        user_id: UUID,
        conversation: AiConversation,
        settings: AiProjectSettings,
        diagram_id: UUID | None,
        requested: RequestedContext,
    ) -> AiProjectContext:
        user = self.db.get(User, user_id)
        permissions = sorted(
            permission.permission_code
            for permission in member.permissions
            if permission.is_allowed
        )
        diagram_context = None
        if requested.include_diagram and diagram_id is not None:
            diagram = self.uml.get_diagram(diagram_id)
            if diagram is None or diagram.project_id != project.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Diagrama no encontrado en el proyecto",
                )
            classes = self.uml.list_classes(diagram.id)
            diagram_context = DiagramContext(
                id=diagram.id,
                name=diagram.name,
                current_version=diagram.current_version,
                classes=[self._serialize_class(item) for item in classes],
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
                    for item in self.uml.list_relationships(diagram.id)
                ],
            )
        recent_messages: list[RecentMessageContext] = []
        if requested.include_recent_messages:
            messages = self.assistant.list_messages(
                conversation.id,
                before_sequence=None,
                after_sequence=None,
                limit=settings.max_context_messages,
            )
            recent_messages = [
                RecentMessageContext(
                    sequence_number=item.sequence_number,
                    role=item.role,
                    content=item.content,
                )
                for item in messages
            ]
        versions: list[dict] = []
        if requested.include_project_versions:
            records = self.db.scalars(
                select(ProjectVersion)
                .where(ProjectVersion.project_id == project.id)
                .order_by(ProjectVersion.version_number.desc())
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
        pending_actions = self.assistant.list_actions(project.id, "proposed", 50)
        pending_recommendations = self.assistant.list_recommendations(
            project.id, "open", None, 50
        )
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
        return AiProjectContext(
            project=ProjectContext(
                id=project.id,
                name=project.name,
                description=project.description,
            ),
            actor=ActorContext(
                id=user_id,
                display_name=user.full_name if user else "Usuario",
                project_role=member.project_role,
                permissions=permissions,
            ),
            active_diagram=diagram_context,
            recent_messages=recent_messages,
            conversation_summary=self._project_conversation_memory(
                project.id, conversation
            ),
            available_versions=versions,
            generation_state=generation_state,
            constraints=ContextConstraints(
                language="es",
                offline=True,
                require_confirmation=settings.require_confirmation,
                surface=requested.surface,
            ),
        )

    def _project_conversation_memory(
        self, project_id: UUID, current: AiConversation
    ) -> str | None:
        sections: list[str] = []
        for conversation in self.assistant.list_conversations(project_id):
            if conversation.summary:
                memory = conversation.summary
            elif conversation.id != current.id:
                messages = self.assistant.list_messages(
                    conversation.id,
                    before_sequence=None,
                    after_sequence=None,
                    limit=20,
                )
                memory = "\n".join(
                    f"{item.role}: {sanitize_untrusted_text(item.content, 600)}"
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

    @staticmethod
    def _serialize_class(item) -> dict:
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
