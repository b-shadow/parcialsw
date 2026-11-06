from datetime import UTC, datetime
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.modules.acceso_usuarios.models import Usuario
from app.modules.asistente_proyecto.models import (
    AccionIA,
    ConfiguracionIAProyecto,
    ConversacionIA,
    MensajeIA,
    RecomendacionIA,
)
from app.modules.asistente_proyecto.services.almacen_documentos_conversacion import (
    AlmacenSincronoDocumentosConversacion,
    encolar_documento_mensaje,
    hash_contenido_mensaje,
)
from app.modules.proyectos_colaboracion.models import Proyecto


class RepositorioAsistente:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.messages = AlmacenSincronoDocumentosConversacion()

    def obtener_configuracion(self, project_id: UUID) -> ConfiguracionIAProyecto | None:
        project = self.db.get(Proyecto, project_id)
        if project is None:
            return None
        data = (project.settings or {}).get("ai", {})
        if not isinstance(data, dict):
            data = {}
        fields = {
            "enabled", "preferred_provider", "model_name", "fallback_enabled",
            "require_confirmation", "max_context_messages", "summary_trigger_messages",
            "settings_json",
        }
        ai_settings = {key: value for key, value in data.items() if key in fields}
        extra = ai_settings.get("settings_json")
        if not isinstance(extra, dict):
            extra = {}
        ai_settings["settings_json"] = {
            **extra,
            "origen_ollama": extra.get("origen_ollama", settings.ollama_default_source),
        }
        return ConfiguracionIAProyecto(
            id=UUID(str(data["id"])) if data.get("id") else uuid5(project_id, "ai-settings"),
            project_id=project_id,
            created_by_user_id=UUID(str(data.get("created_by_user_id", project.owner_id))),
            updated_by_user_id=UUID(str(data.get("updated_by_user_id", project.owner_id))),
            created_at=datetime.fromisoformat(data.get("created_at", project.created_at.isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", project.updated_at.isoformat())),
            **ai_settings,
        )

    def obtener_conversacion(
        self, project_id: UUID, conversation_id: UUID | None = None, for_update: bool = False
    ) -> ConversacionIA | None:
        statement = select(ConversacionIA).where(ConversacionIA.project_id == project_id)
        if conversation_id is not None:
            statement = statement.where(ConversacionIA.id == conversation_id)
        else:
            statement = statement.order_by(ConversacionIA.updated_at.desc())
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def listar_conversaciones(self, project_id: UUID) -> list[ConversacionIA]:
        return list(
            self.db.scalars(
                select(ConversacionIA)
                .where(ConversacionIA.project_id == project_id)
                .order_by(ConversacionIA.updated_at.desc())
            )
        )

    def obtener_mensaje_por_id_cliente(
        self, conversation_id: UUID, author_user_id: UUID, client_message_id: UUID
    ) -> MensajeIA | None:
        if settings.nosql_consolidated_mode:
            return self.messages.obtener_por_id_cliente(conversation_id, author_user_id, client_message_id)
        return self.db.scalar(
            select(MensajeIA).where(
                MensajeIA.conversation_id == conversation_id,
                MensajeIA.author_user_id == author_user_id,
                MensajeIA.client_message_id == client_message_id,
            )
        )

    def obtener_mensaje_asistente_por_correlacion(
        self, conversation_id: UUID, correlation_id: UUID
    ) -> MensajeIA | None:
        if settings.nosql_consolidated_mode:
            return self.messages.obtener_asistente_por_correlacion(conversation_id, correlation_id)
        return self.db.scalar(
            select(MensajeIA).where(
                MensajeIA.conversation_id == conversation_id,
                MensajeIA.correlation_id == correlation_id,
                MensajeIA.role == "assistant",
            )
        )

    def listar_mensajes(
        self,
        conversation_id: UUID,
        *,
        before_sequence: int | None,
        after_sequence: int | None,
        limit: int,
    ) -> list[MensajeIA]:
        if settings.nosql_consolidated_mode:
            return self.messages.listar_mensajes(
                conversation_id,
                before_sequence=before_sequence,
                after_sequence=after_sequence,
                limit=limit,
            )
        statement = select(MensajeIA).where(MensajeIA.conversation_id == conversation_id)
        if before_sequence is not None:
            statement = statement.where(MensajeIA.sequence_number < before_sequence)
        if after_sequence is not None:
            statement = statement.where(MensajeIA.sequence_number > after_sequence)
        if after_sequence is not None:
            statement = statement.order_by(MensajeIA.sequence_number).limit(limit)
            return list(self.db.scalars(statement))
        statement = statement.order_by(MensajeIA.sequence_number.desc()).limit(limit)
        return list(reversed(list(self.db.scalars(statement))))

    def existe_mensaje_anterior(self, conversation_id: UUID, sequence: int) -> bool:
        if settings.nosql_consolidated_mode:
            return self.messages.existe_anterior(conversation_id, sequence)
        return (
            self.db.scalar(
                select(MensajeIA.id)
                .where(
                    MensajeIA.conversation_id == conversation_id,
                    MensajeIA.sequence_number < sequence,
                )
                .limit(1)
            )
            is not None
        )

    def existe_mensaje_posterior(self, conversation_id: UUID, sequence: int) -> bool:
        if settings.nosql_consolidated_mode:
            return self.messages.existe_posterior(conversation_id, sequence)
        return (
            self.db.scalar(
                select(MensajeIA.id)
                .where(
                    MensajeIA.conversation_id == conversation_id,
                    MensajeIA.sequence_number > sequence,
                )
                .limit(1)
            )
            is not None
        )

    def obtener_mensaje(self, message_id: UUID):
        if settings.nosql_consolidated_mode:
            return self.messages.obtener(message_id)
        return self.db.get(MensajeIA, message_id)

    def guardar_mensaje(self, message) -> None:
        if settings.nosql_consolidated_mode:
            message.updated_at = datetime.now(UTC)
            message.content_hash = hash_contenido_mensaje(message)
            self.messages.guardar_o_actualizar(message)
            return
        encolar_documento_mensaje(self.db, message)

    def nombres_visibles_usuarios(self, user_ids: set[UUID]) -> dict[UUID, str]:
        if not user_ids:
            return {}
        users = self.db.scalars(select(Usuario).where(Usuario.id.in_(user_ids)))
        return {user.id: user.full_name or user.email for user in users}

    def listar_acciones(
        self,
        project_id: UUID,
        status: str | None,
        limit: int,
        conversation_id: UUID | None = None,
    ) -> list[AccionIA]:
        statement = select(AccionIA).where(AccionIA.project_id == project_id)
        if conversation_id is not None:
            statement = statement.where(AccionIA.conversation_id == conversation_id)
        if status:
            statement = statement.where(AccionIA.status == status)
        return list(self.db.scalars(statement.order_by(AccionIA.created_at.desc()).limit(limit)))

    def obtener_accion(
        self, project_id: UUID, action_id: UUID, *, for_update: bool = False
    ) -> AccionIA | None:
        statement = select(AccionIA).where(
            AccionIA.project_id == project_id, AccionIA.id == action_id
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def obtener_accion_por_idempotencia(self, project_id: UUID, key: UUID) -> AccionIA | None:
        return self.db.scalar(
            select(AccionIA).where(
                AccionIA.project_id == project_id,
                AccionIA.idempotency_key == key,
            )
        )

    def listar_acciones_por_mensaje(self, message_id: UUID) -> list[AccionIA]:
        acciones = list(
            self.db.scalars(
                select(AccionIA)
                .where(AccionIA.source_message_id == message_id)
                .order_by(AccionIA.created_at)
            )
        )
        return sorted(acciones, key=lambda accion: (accion.payload.get("_plan") or {}).get("order", 0))

    def listar_recomendaciones_por_mensaje(self, message_id: UUID) -> list[RecomendacionIA]:
        return list(
            self.db.scalars(
                select(RecomendacionIA)
                .where(RecomendacionIA.source_message_id == message_id)
                .order_by(RecomendacionIA.created_at)
            )
        )

    def listar_recomendaciones(
        self,
        project_id: UUID,
        status: str | None,
        severity: str | None,
        limit: int,
        conversation_id: UUID | None = None,
    ) -> list[RecomendacionIA]:
        statement = select(RecomendacionIA).where(RecomendacionIA.project_id == project_id)
        if conversation_id is not None:
            statement = statement.where(RecomendacionIA.conversation_id == conversation_id)
        if status:
            statement = statement.where(RecomendacionIA.status == status)
        if severity:
            statement = statement.where(RecomendacionIA.severity == severity)
        return list(
            self.db.scalars(statement.order_by(RecomendacionIA.created_at.desc()).limit(limit))
        )

    def obtener_recomendacion(
        self, project_id: UUID, recommendation_id: UUID, *, for_update: bool = False
    ) -> RecomendacionIA | None:
        statement = select(RecomendacionIA).where(
            RecomendacionIA.project_id == project_id,
            RecomendacionIA.id == recommendation_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)
