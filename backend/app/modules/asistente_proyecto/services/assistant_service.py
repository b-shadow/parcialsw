import logging
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.nosql.contracts import AiMessageDocument
from app.modules.asistente_proyecto.models import AiConversation, AiMessage, AiProjectSettings
from app.modules.asistente_proyecto.repositories.assistant_repository import AssistantRepository
from app.modules.asistente_proyecto.schemas import (
    AiConversationCreate,
    AiConversationUpdate,
    AiMessageCreateInternal,
    AiMessagePage,
    AiMessageResponse,
    AiProjectSettingsUpdate,
    AiRecommendationStatusUpdate,
)
from app.modules.asistente_proyecto.services.conversation_document_store import (
    ConversationDocumentStore,
    SyncConversationDocumentStore,
    enqueue_message_document,
    message_content_hash,
)
from app.modules.proyectos_colaboracion.models import Project
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.repositories.project_repository import ProjectRepository
from app.modules.proyectos_colaboracion.services.project_mutation_guard import ProjectMutationGuard
from app.modules.proyectos_colaboracion.validators.project_validator import (
    ensure_membership,
    ensure_project_exists,
    ensure_project_permission,
)

logger = logging.getLogger(__name__)


class AssistantContractService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AssistantRepository(db)
        self.projects = ProjectRepository(db)
        self.members = MemberRepository(db)
        self.documents = ConversationDocumentStore()
        self.sync_documents = SyncConversationDocumentStore()

    def _project_and_member(self, project_id: UUID, user_id: UUID):
        project = ensure_project_exists(self.projects.get(project_id))
        member = ensure_membership(self.members.get_membership(project_id, user_id))
        return project, member

    @staticmethod
    def _can_organize(project: Project, member, user_id: UUID) -> bool:
        return project.owner_id == user_id or member.project_role == "ORGANIZADOR"

    def get_settings(self, project_id: UUID, user_id: UUID) -> AiProjectSettings:
        self._project_and_member(project_id, user_id)
        settings = self.repository.get_settings(project_id)
        if settings is not None:
            return settings
        settings = AiProjectSettings(
            project_id=project_id,
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
        )
        self.db.add(settings)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            settings = self.repository.get_settings(project_id)
            if settings is None:
                raise
        self.db.refresh(settings)
        return settings

    def update_settings(
        self, project_id: UUID, user_id: UUID, payload: AiProjectSettingsUpdate
    ) -> AiProjectSettings:
        ensure_project_permission(self.db, project_id, user_id, "ai.settings")
        _project, _member = self._project_and_member(project_id, user_id)
        locked_project = ProjectMutationGuard(self.db).acquire(project_id)
        settings = self.repository.get_settings(project_id)
        values = payload.model_dump()
        changed = settings is None or any(
            getattr(settings, field) != value for field, value in values.items()
        )
        if settings is None:
            settings = AiProjectSettings(
                project_id=project_id,
                created_by_user_id=user_id,
                updated_by_user_id=user_id,
            )
            self.db.add(settings)
        for field, value in values.items():
            setattr(settings, field, value)
        settings.updated_by_user_id = user_id
        if changed:
            ProjectMutationGuard.advance(locked_project)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def list_conversations(self, project_id: UUID, user_id: UUID) -> list[AiConversation]:
        self._project_and_member(project_id, user_id)
        return self.repository.list_conversations(project_id)

    def create_conversation(
        self, project_id: UUID, user_id: UUID, payload: AiConversationCreate
    ) -> AiConversation:
        self._project_and_member(project_id, user_id)
        conversation = AiConversation(
            project_id=project_id,
            title=payload.title,
            created_by_user_id=user_id,
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def update_conversation(
        self,
        project_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        payload: AiConversationUpdate,
    ) -> AiConversation:
        self._project_and_member(project_id, user_id)
        conversation = self.repository.get_conversation(project_id, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Chat no encontrado en el proyecto")
        conversation.title = payload.title
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(
        self, project_id: UUID, user_id: UUID, conversation_id: UUID | None = None
    ) -> AiConversation:
        self._project_and_member(project_id, user_id)
        conversation = self.repository.get_conversation(project_id, conversation_id)
        if conversation is not None:
            return conversation
        if conversation_id is not None:
            raise HTTPException(status_code=404, detail="Chat no encontrado en el proyecto")
        conversation = AiConversation(
            project_id=project_id,
            title="Chat principal",
            created_by_user_id=user_id,
        )
        self.db.add(conversation)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            conversation = self.repository.get_conversation(project_id)
            if conversation is None:
                raise
        self.db.refresh(conversation)
        return conversation

    def create_message(
        self,
        project_id: UUID,
        user_id: UUID | None,
        payload: AiMessageCreateInternal,
        conversation_id: UUID | None = None,
    ) -> tuple[AiMessage, bool]:
        if user_id is not None:
            self._project_and_member(project_id, user_id)
            if payload.role == "user":
                ensure_project_permission(self.db, project_id, user_id, "ai.chat")
        conversation = self.repository.get_conversation(project_id, conversation_id)
        if conversation is None:
            if user_id is None:
                raise HTTPException(status_code=409, detail="La conversacion todavia no existe")
            conversation = self.get_conversation(project_id, user_id, conversation_id)
        if payload.role == "user" and user_id is None:
            raise HTTPException(status_code=422, detail="Un mensaje de usuario requiere autor")
        if payload.client_message_id is not None and user_id is not None:
            existing = self.repository.get_message_by_client_id(
                conversation.id, user_id, payload.client_message_id
            )
            if existing is not None:
                return existing, False

        conversation = self.repository.get_conversation(
            project_id, conversation.id, for_update=True
        )
        if conversation is None:
            raise HTTPException(status_code=409, detail="La conversacion no esta disponible")
        if payload.client_message_id is not None and user_id is not None:
            existing = self.repository.get_message_by_client_id(
                conversation.id, user_id, payload.client_message_id
            )
            if existing is not None:
                return existing, False
        self._validate_references(project_id, payload)
        conversation.last_message_sequence += 1
        values = {
            "conversation_id": conversation.id,
            "project_id": project_id,
            "author_user_id": user_id,
            "role": payload.role,
            "content": payload.content.strip(),
            "sequence_number": conversation.last_message_sequence,
            "client_message_id": payload.client_message_id,
            "correlation_id": payload.correlation_id,
            "status": payload.status,
            "detected_intents": [
                item.name if hasattr(item, "name") else str(item)
                for item in payload.detected_intents
            ],
            "references_json": [item.model_dump(mode="json") for item in payload.references],
            "metadata_json": payload.metadata_json,
        }
        if settings.nosql_consolidated_mode:
            message = AiMessageDocument(_id=uuid4(), content_hash="0" * 64, **values)
            message.content_hash = message_content_hash(message)
            self.sync_documents.upsert(message)
        else:
            message = AiMessage(**values)
            self.db.add(message)
            enqueue_message_document(self.db, message)
        if conversation.last_message_sequence == 1 and conversation.title in {
            "Nuevo chat",
            "Chat principal",
        }:
            conversation.title = self._title_from_first_message(payload.content)
        self.db.commit()
        if not settings.nosql_consolidated_mode:
            self.db.refresh(message)
        return message, True

    @staticmethod
    def _title_from_first_message(content: str) -> str:
        normalized = re.sub(r"\s+", " ", content).strip()
        words = normalized.split(" ")[:8]
        title = " ".join(words).strip(" .,:;!?-_")
        return title[:80] or "Nuevo chat"

    async def list_messages(
        self,
        project_id: UUID,
        user_id: UUID,
        before_sequence: int | None,
        after_sequence: int | None,
        limit: int,
        conversation_id: UUID | None = None,
    ) -> AiMessagePage:
        if before_sequence is not None and after_sequence is not None:
            raise HTTPException(
                status_code=422, detail="Use before_sequence o after_sequence, no ambos"
            )
        conversation = self.get_conversation(project_id, user_id, conversation_id)
        sql_items = (
            self.repository.list_messages(
                conversation.id,
                before_sequence=before_sequence,
                after_sequence=after_sequence,
                limit=max(1, min(limit, 100)),
            )
            if settings.ai_messages_sql_fallback_enabled or settings.ai_messages_compare_reads
            else []
        )
        mongo_items = await self.documents.safe_list_messages(
            conversation.id,
            before_sequence=before_sequence,
            after_sequence=after_sequence,
            limit=max(1, min(limit, 100)),
        )
        items = self._effective_messages(
            sql_items,
            mongo_items,
            limit=max(1, min(limit, 100)),
            after_sequence=after_sequence,
        )
        author_ids = {item.author_user_id for item in items if item.author_user_id}
        display_names = self.repository.user_display_names(author_ids)
        responses = [
            AiMessageResponse.model_validate(item).model_copy(
                update={
                    "author_display_name": (
                        display_names.get(item.author_user_id)
                        if item.author_user_id
                        else "Asistente CASE"
                    )
                }
            )
            for item in items
        ]
        mongo_before = (
            await self.documents.safe_message_exists_before(
                conversation.id, items[0].sequence_number
            )
            if mongo_items is not None and items
            else False
        )
        mongo_after = (
            await self.documents.safe_message_exists_after(
                conversation.id, items[-1].sequence_number
            )
            if mongo_items is not None and items
            else False
        )
        return AiMessagePage(
            items=responses,
            previous_cursor=items[0].sequence_number if items else None,
            next_cursor=items[-1].sequence_number if items else None,
            has_more_before=(
                mongo_before
                or (
                    settings.ai_messages_sql_fallback_enabled
                    and self.repository.message_exists_before(
                        conversation.id, items[0].sequence_number
                    )
                )
                if items
                else False
            ),
            has_more_after=(
                mongo_after
                or (
                    settings.ai_messages_sql_fallback_enabled
                    and self.repository.message_exists_after(
                        conversation.id, items[-1].sequence_number
                    )
                )
                if items
                else False
            ),
            min_sequence=items[0].sequence_number if items else None,
            max_sequence=items[-1].sequence_number if items else None,
        )

    @staticmethod
    def _effective_messages(sql_items, mongo_items, *, limit: int, after_sequence: int | None):
        if mongo_items is None:
            return sql_items
        by_sequence = {item.sequence_number: item for item in mongo_items}
        missing_in_mongo = []
        mismatches = []
        for item in sql_items:
            document = by_sequence.get(item.sequence_number)
            if document is None:
                by_sequence[item.sequence_number] = item
                missing_in_mongo.append(item.id)
            elif message_content_hash(item) != document.content_hash:
                mismatches.append(item.id)
        if (missing_in_mongo or mismatches) and settings.ai_messages_compare_reads:
            logger.warning(
                "ai_message_store_drift",
                extra={
                    "missing_in_mongo": [str(item) for item in missing_in_mongo],
                    "hash_mismatches": [str(item) for item in mismatches],
                },
            )
        ordered = sorted(by_sequence.values(), key=lambda item: item.sequence_number)
        return ordered[:limit] if after_sequence is not None else ordered[-limit:]

    def list_actions(
        self,
        project_id: UUID,
        user_id: UUID,
        action_status: str | None,
        limit: int,
        conversation_id: UUID | None = None,
    ):
        self._project_and_member(project_id, user_id)
        return self.repository.list_actions(
            project_id, action_status, max(1, min(limit, 200)), conversation_id
        )

    def get_action(self, project_id: UUID, action_id: UUID, user_id: UUID):
        self._project_and_member(project_id, user_id)
        action = self.repository.get_action(project_id, action_id)
        if action is None:
            raise HTTPException(status_code=404, detail="Accion de IA no encontrada")
        return action

    def list_recommendations(
        self,
        project_id: UUID,
        user_id: UUID,
        item_status: str | None,
        severity: str | None,
        limit: int,
        conversation_id: UUID | None = None,
    ):
        self._project_and_member(project_id, user_id)
        return self.repository.list_recommendations(
            project_id, item_status, severity, max(1, min(limit, 200)), conversation_id
        )

    def update_recommendation(
        self,
        project_id: UUID,
        recommendation_id: UUID,
        user_id: UUID,
        payload: AiRecommendationStatusUpdate,
    ):
        self._project_and_member(project_id, user_id)
        recommendation = self.repository.get_recommendation(
            project_id, recommendation_id, for_update=True
        )
        if recommendation is None:
            raise HTTPException(status_code=404, detail="Recomendacion no encontrada")
        if recommendation.status == payload.status:
            return recommendation
        if recommendation.status == "resolved":
            raise HTTPException(status_code=409, detail="La recomendacion ya esta resuelta")
        recommendation.status = payload.status
        recommendation.resolution_note = payload.resolution_note
        recommendation.resolved_by_user_id = user_id
        recommendation.resolved_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(recommendation)
        return recommendation

    def _validate_references(self, project_id: UUID, payload: AiMessageCreateInternal) -> None:
        from app.modules.generacion_software.models import (
            GeneratedBackend,
            GeneratedFrontend,
            UmlTransformation,
        )
        from app.modules.modelado_uml.models import (
            UmlClass,
            UmlDiagram,
            UmlMethod,
            UmlRelationship,
        )
        from app.modules.proyectos_colaboracion.models import ProjectVersion

        document_uml = None
        if settings.nosql_consolidated_mode:
            from app.modules.modelado_uml.repositories.mongo_uml_repository import (
                MongoUmlRepository,
            )

            document_uml = MongoUmlRepository(self.db)

        for reference in payload.references:
            belongs = False
            if reference.type == "uml_class":
                item = (
                    document_uml.get_class(reference.id)
                    if document_uml
                    else self.db.get(UmlClass, reference.id)
                )
                diagram = self.db.get(UmlDiagram, item.diagram_id) if item else None
                belongs = diagram is not None and diagram.project_id == project_id
            elif reference.type == "uml_method":
                item = (
                    document_uml.get_method(reference.id)
                    if document_uml
                    else self.db.get(UmlMethod, reference.id)
                )
                uml_class = (
                    document_uml.get_class(item.class_id)
                    if document_uml and item
                    else self.db.get(UmlClass, item.class_id) if item else None
                )
                diagram = self.db.get(UmlDiagram, uml_class.diagram_id) if uml_class else None
                belongs = diagram is not None and diagram.project_id == project_id
            elif reference.type == "uml_relationship":
                item = (
                    document_uml.get_relationship(reference.id)
                    if document_uml
                    else self.db.get(UmlRelationship, reference.id)
                )
                belongs = item is not None and item.diagram_id in {
                    diagram.id
                    for diagram in self.db.scalars(
                        select(UmlDiagram).where(UmlDiagram.project_id == project_id)
                    )
                }
            elif reference.type == "project_version":
                item = self.db.get(ProjectVersion, reference.id)
                belongs = item is not None and item.project_id == project_id
            elif reference.type == "generation":
                item = (
                    self.db.get(UmlTransformation, reference.id)
                    or self.db.get(GeneratedBackend, reference.id)
                    or self.db.get(GeneratedFrontend, reference.id)
                )
                belongs = item is not None and item.project_id == project_id
            if not belongs:
                raise HTTPException(
                    status_code=422,
                    detail="Una referencia de IA no pertenece al proyecto",
                )
