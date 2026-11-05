import logging
import re
from datetime import UTC, datetime
from itertools import pairwise
from uuid import UUID, uuid4, uuid5

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.core.nosql.contratos import DocumentoMensajeIA
from app.modules.asistente_proyecto.models import ConfiguracionIAProyecto, ConversacionIA, MensajeIA
from app.modules.asistente_proyecto.repositories.repositorio_asistente import RepositorioAsistente
from app.modules.asistente_proyecto.schemas import (
    ActualizacionConfiguracionIAProyecto,
    ActualizacionConversacionIA,
    ActualizacionEstadoRecomendacionIA,
    CreacionConversacionIA,
    CreacionInternaMensajeIA,
    PaginaMensajesIA,
    RespuestaMensajeIA,
)
from app.modules.asistente_proyecto.services.almacen_documentos_conversacion import (
    AlmacenDocumentosConversacion,
    AlmacenSincronoDocumentosConversacion,
    encolar_documento_mensaje,
    hash_contenido_mensaje,
)
from app.modules.proyectos_colaboracion.models import Proyecto
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

logger = logging.getLogger(__name__)


class ServicioContratoAsistente:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = RepositorioAsistente(db)
        self.projects = RepositorioProyectos(db)
        self.members = RepositorioIntegrantes(db)
        self.documents = AlmacenDocumentosConversacion()
        self.sync_documents = AlmacenSincronoDocumentosConversacion()

    def _proyecto_y_miembro(self, project_id: UUID, user_id: UUID):
        project = asegurar_proyecto_existente(self.projects.get(project_id))
        member = asegurar_participacion(self.members.obtener_participacion(project_id, user_id))
        return project, member

    @staticmethod
    def _puede_organizar(project: Proyecto, member, user_id: UUID) -> bool:
        return project.owner_id == user_id or member.project_role == "ORGANIZADOR"

    def obtener_configuracion(self, project_id: UUID, user_id: UUID) -> ConfiguracionIAProyecto:
        self._proyecto_y_miembro(project_id, user_id)
        return self.repository.obtener_configuracion(project_id)

    def actualizar_configuracion(
        self, project_id: UUID, user_id: UUID, payload: ActualizacionConfiguracionIAProyecto
    ) -> ConfiguracionIAProyecto:
        asegurar_permiso_proyecto(self.db, project_id, user_id, "ai.settings")
        _project, _member = self._proyecto_y_miembro(project_id, user_id)
        locked_project = GuardiaMutacionesProyecto(self.db).acquire(project_id)
        values = payload.model_dump()
        old = (locked_project.settings or {}).get("ai", {})
        changed = any(old.get(key) != value for key, value in values.items())
        if changed:
            now = datetime.now(UTC).isoformat()
            locked_project.settings = {
                **(locked_project.settings or {}),
                "ai": {
                    **values,
                    "id": old.get("id", str(uuid5(project_id, "ai-settings"))),
                    "created_by_user_id": old.get("created_by_user_id", str(user_id)),
                    "updated_by_user_id": str(user_id),
                    "created_at": old.get("created_at", now),
                    "updated_at": now,
                },
            }
            GuardiaMutacionesProyecto.avanzar(locked_project)
        self.db.commit()
        return self.repository.obtener_configuracion(project_id)

    def listar_conversaciones(self, project_id: UUID, user_id: UUID) -> list[ConversacionIA]:
        self._proyecto_y_miembro(project_id, user_id)
        return self.repository.listar_conversaciones(project_id)

    def crear_conversacion(
        self, project_id: UUID, user_id: UUID, payload: CreacionConversacionIA
    ) -> ConversacionIA:
        self._proyecto_y_miembro(project_id, user_id)
        conversation = ConversacionIA(
            project_id=project_id,
            title=payload.title,
            created_by_user_id=user_id,
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def actualizar_conversacion(
        self,
        project_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        payload: ActualizacionConversacionIA,
    ) -> ConversacionIA:
        self._proyecto_y_miembro(project_id, user_id)
        conversation = self.repository.obtener_conversacion(project_id, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Chat no encontrado en el proyecto")
        conversation.title = payload.title
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def obtener_conversacion(
        self, project_id: UUID, user_id: UUID, conversation_id: UUID | None = None
    ) -> ConversacionIA:
        self._proyecto_y_miembro(project_id, user_id)
        conversation = self.repository.obtener_conversacion(project_id, conversation_id)
        if conversation is not None:
            return conversation
        if conversation_id is not None:
            raise HTTPException(status_code=404, detail="Chat no encontrado en el proyecto")
        conversation = ConversacionIA(
            project_id=project_id,
            title="Chat principal",
            created_by_user_id=user_id,
        )
        self.db.add(conversation)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            conversation = self.repository.obtener_conversacion(project_id)
            if conversation is None:
                raise
        self.db.refresh(conversation)
        return conversation

    def crear_mensaje(
        self,
        project_id: UUID,
        user_id: UUID | None,
        payload: CreacionInternaMensajeIA,
        conversation_id: UUID | None = None,
    ) -> tuple[MensajeIA, bool]:
        if user_id is not None:
            self._proyecto_y_miembro(project_id, user_id)
            if payload.role == "user":
                asegurar_permiso_proyecto(self.db, project_id, user_id, "ai.chat")
        conversation = self.repository.obtener_conversacion(project_id, conversation_id)
        if conversation is None:
            if user_id is None:
                raise HTTPException(status_code=409, detail="La conversacion todavia no existe")
            conversation = self.obtener_conversacion(project_id, user_id, conversation_id)
        if payload.role == "user" and user_id is None:
            raise HTTPException(status_code=422, detail="Un mensaje de usuario requiere autor")
        if payload.client_message_id is not None and user_id is not None:
            existing = self.repository.obtener_mensaje_por_id_cliente(
                conversation.id, user_id, payload.client_message_id
            )
            if existing is not None:
                return existing, False

        conversation = self.repository.obtener_conversacion(
            project_id, conversation.id, for_update=True
        )
        if conversation is None:
            raise HTTPException(status_code=409, detail="La conversacion no esta disponible")
        if payload.client_message_id is not None and user_id is not None:
            existing = self.repository.obtener_mensaje_por_id_cliente(
                conversation.id, user_id, payload.client_message_id
            )
            if existing is not None:
                return existing, False
        self._validar_referencias(project_id, payload)
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
            message = DocumentoMensajeIA(_id=uuid4(), content_hash="0" * 64, **values)
            message.content_hash = hash_contenido_mensaje(message)
            self.sync_documents.guardar_o_actualizar(message)
        else:
            message = MensajeIA(**values)
            self.db.add(message)
            encolar_documento_mensaje(self.db, message)
        if conversation.last_message_sequence == 1 and conversation.title in {
            "Nuevo chat",
            "Chat principal",
        }:
            conversation.title = self._titulo_desde_primer_mensaje(payload.content)
        self.db.commit()
        if not settings.nosql_consolidated_mode:
            self.db.refresh(message)
        return message, True

    @staticmethod
    def _titulo_desde_primer_mensaje(content: str) -> str:
        normalized = re.sub(r"\s+", " ", content).strip()
        words = normalized.split(" ")[:8]
        title = " ".join(words).strip(" .,:;!?-_")
        return title[:80] or "Nuevo chat"

    async def listar_mensajes(
        self,
        project_id: UUID,
        user_id: UUID,
        before_sequence: int | None,
        after_sequence: int | None,
        limit: int,
        conversation_id: UUID | None = None,
    ) -> PaginaMensajesIA:
        if before_sequence is not None and after_sequence is not None:
            raise HTTPException(
                status_code=422, detail="Use before_sequence o after_sequence, no ambos"
            )
        conversation = self.obtener_conversacion(project_id, user_id, conversation_id)
        sql_items = (
            self.repository.listar_mensajes(
                conversation.id,
                before_sequence=before_sequence,
                after_sequence=after_sequence,
                limit=max(1, min(limit, 100)),
            )
            if settings.ai_messages_sql_fallback_enabled or settings.ai_messages_compare_reads
            else []
        )
        mongo_items = await self.documents.listar_mensajes_seguro(
            conversation.id,
            before_sequence=before_sequence,
            after_sequence=after_sequence,
            limit=max(1, min(limit, 100)),
        )
        if settings.nosql_consolidated_mode and mongo_items is not None:
            sequences = [item.sequence_number for item in mongo_items]
            missing_history = (
                before_sequence is None
                and after_sequence is None
                and conversation.last_message_sequence > 0
                and (not sequences or sequences[-1] != conversation.last_message_sequence)
            )
            missing_page = any(
                following != current + 1
                for current, following in pairwise(sequences)
            )
        else:
            missing_history = False
            missing_page = False
        if missing_history or missing_page:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "CONVERSATION_MESSAGES_MISSING",
                    "message": "El historial de este chat no esta disponible en MongoDB",
                },
            )
        items = self._mensajes_efectivos(
            sql_items,
            mongo_items,
            limit=max(1, min(limit, 100)),
            after_sequence=after_sequence,
        )
        author_ids = {item.author_user_id for item in items if item.author_user_id}
        display_names = self.repository.nombres_visibles_usuarios(author_ids)
        responses = [
            RespuestaMensajeIA.model_validate(item).model_copy(
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
            await self.documents.existe_mensaje_anterior_seguro(
                conversation.id, items[0].sequence_number
            )
            if mongo_items is not None and items
            else False
        )
        mongo_after = (
            await self.documents.existe_mensaje_posterior_seguro(
                conversation.id, items[-1].sequence_number
            )
            if mongo_items is not None and items
            else False
        )
        return PaginaMensajesIA(
            items=responses,
            previous_cursor=items[0].sequence_number if items else None,
            next_cursor=items[-1].sequence_number if items else None,
            has_more_before=(
                mongo_before
                or (
                    settings.ai_messages_sql_fallback_enabled
                    and self.repository.existe_mensaje_anterior(
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
                    and self.repository.existe_mensaje_posterior(
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
    def _mensajes_efectivos(sql_items, mongo_items, *, limit: int, after_sequence: int | None):
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
            elif hash_contenido_mensaje(item) != document.content_hash:
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

    def listar_acciones(
        self,
        project_id: UUID,
        user_id: UUID,
        action_status: str | None,
        limit: int,
        conversation_id: UUID | None = None,
    ):
        self._proyecto_y_miembro(project_id, user_id)
        return self.repository.listar_acciones(
            project_id, action_status, max(1, min(limit, 200)), conversation_id
        )

    def obtener_accion(self, project_id: UUID, action_id: UUID, user_id: UUID):
        self._proyecto_y_miembro(project_id, user_id)
        action = self.repository.obtener_accion(project_id, action_id)
        if action is None:
            raise HTTPException(status_code=404, detail="Accion de IA no encontrada")
        return action

    def listar_recomendaciones(
        self,
        project_id: UUID,
        user_id: UUID,
        item_status: str | None,
        severity: str | None,
        limit: int,
        conversation_id: UUID | None = None,
    ):
        self._proyecto_y_miembro(project_id, user_id)
        return self.repository.listar_recomendaciones(
            project_id, item_status, severity, max(1, min(limit, 200)), conversation_id
        )

    def actualizar_recomendacion(
        self,
        project_id: UUID,
        recommendation_id: UUID,
        user_id: UUID,
        payload: ActualizacionEstadoRecomendacionIA,
    ):
        self._proyecto_y_miembro(project_id, user_id)
        recommendation = self.repository.obtener_recomendacion(
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

    def _validar_referencias(self, project_id: UUID, payload: CreacionInternaMensajeIA) -> None:
        from app.modules.generacion_software.models import (
            BackendGenerado,
            FrontendGenerado,
            TransformacionUML,
        )
        from app.modules.modelado_uml.models import (
            ClaseUML,
            DiagramaUML,
            MetodoUML,
            RelacionUML,
        )
        from app.modules.proyectos_colaboracion.models import VersionProyecto

        document_uml = None
        if settings.nosql_consolidated_mode:
            from app.modules.modelado_uml.repositories.repositorio_mongo_uml import (
                RepositorioMongoUML,
            )

            document_uml = RepositorioMongoUML(self.db)

        for reference in payload.references:
            belongs = False
            if reference.type == "uml_class":
                item = (
                    document_uml.obtener_clase(reference.id)
                    if document_uml
                    else self.db.get(ClaseUML, reference.id)
                )
                diagram = self.db.get(DiagramaUML, item.diagram_id) if item else None
                belongs = diagram is not None and diagram.project_id == project_id
            elif reference.type == "uml_method":
                item = (
                    document_uml.obtener_metodo(reference.id)
                    if document_uml
                    else self.db.get(MetodoUML, reference.id)
                )
                uml_class = (
                    document_uml.obtener_clase(item.class_id)
                    if document_uml and item
                    else self.db.get(ClaseUML, item.class_id) if item else None
                )
                diagram = self.db.get(DiagramaUML, uml_class.diagram_id) if uml_class else None
                belongs = diagram is not None and diagram.project_id == project_id
            elif reference.type == "uml_relationship":
                item = (
                    document_uml.obtener_relacion(reference.id)
                    if document_uml
                    else self.db.get(RelacionUML, reference.id)
                )
                belongs = item is not None and item.diagram_id in {
                    diagram.id
                    for diagram in self.db.scalars(
                        select(DiagramaUML).where(DiagramaUML.project_id == project_id)
                    )
                }
            elif reference.type == "project_version":
                item = self.db.get(VersionProyecto, reference.id)
                belongs = item is not None and item.project_id == project_id
            elif reference.type == "generation":
                item = (
                    self.db.get(TransformacionUML, reference.id)
                    or self.db.get(BackendGenerado, reference.id)
                    or self.db.get(FrontendGenerado, reference.id)
                )
                belongs = item is not None and item.project_id == project_id
            if not belongs:
                raise HTTPException(
                    status_code=422,
                    detail="Una referencia de IA no pertenece al proyecto",
                )
