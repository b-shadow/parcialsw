import json
import logging
from uuid import UUID, uuid4

from ai_engine.context.saneador import sanear_datos_contexto, sanear_texto_no_confiable
from pydantic import BaseModel, Field

from app.core.config.configuracion import settings as app_settings
from app.core.database.sesion import SessionLocal
from app.modules.asistente_proyecto.repositories.repositorio_asistente import RepositorioAsistente
from app.modules.asistente_proyecto.services.almacen_documentos_conversacion import (
    AlmacenDocumentosConversacion,
    documento_instantanea_contexto,
)
from app.modules.asistente_proyecto.services.publicador_eventos import PublicadorEventosIAProyecto
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente

logger = logging.getLogger(__name__)


class ResumenMemoriaConversacion(BaseModel):
    project_goal: str = Field(default="", max_length=1000)
    decisions: list[str] = Field(default_factory=list, max_length=50)
    open_questions: list[str] = Field(default_factory=list, max_length=50)
    recent_changes: list[str] = Field(default_factory=list, max_length=50)
    important_entities: list[str] = Field(default_factory=list, max_length=100)
    pending_actions: list[str] = Field(default_factory=list, max_length=100)
    member_preferences_relevant_to_work: list[str] = Field(default_factory=list, max_length=30)
    summary_until_sequence: int = Field(ge=0)


class ServicioMemoriaConversacion:
    def __init__(self, db) -> None:
        self.db = db
        self.repository = RepositorioAsistente(db)
        self.documents = AlmacenDocumentosConversacion()

    async def resumir_si_es_necesario(
        self,
        project_id: UUID,
        user_id: UUID,
        conversation_id: UUID | None = None,
        *,
        force: bool = False,
    ) -> tuple[ResumenMemoriaConversacion, UUID] | None:
        contracts = ServicioContratoAsistente(self.db)
        settings = contracts.obtener_configuracion(project_id, user_id)
        conversation = contracts.obtener_conversacion(project_id, user_id, conversation_id)
        unsummarized = conversation.last_message_sequence - conversation.summary_until_sequence
        if unsummarized <= 0 or (not force and unsummarized < settings.summary_trigger_messages):
            return None
        initial_boundary = conversation.summary_until_sequence
        sql_messages = (
            self.repository.listar_mensajes(
                conversation.id,
                before_sequence=None,
                after_sequence=initial_boundary,
                limit=min(settings.summary_trigger_messages * 2, 200),
            )
            if app_settings.ai_messages_sql_fallback_enabled
            or app_settings.ai_messages_compare_reads
            else []
        )
        mongo_messages = await self.documents.listar_mensajes_seguro(
            conversation.id,
            before_sequence=None,
            after_sequence=initial_boundary,
            limit=min(settings.summary_trigger_messages * 2, 200),
        )
        if mongo_messages is None:
            messages = sql_messages
        else:
            by_sequence = {item.sequence_number: item for item in mongo_messages}
            for item in sql_messages:
                by_sequence.setdefault(item.sequence_number, item)
            messages = sorted(by_sequence.values(), key=lambda item: item.sequence_number)
        completed = [item for item in messages if item.status == "completed"]
        if not completed or (not force and len(completed) < settings.summary_trigger_messages):
            return None
        target_sequence = completed[-1].sequence_number
        conversation_id = conversation.id
        previous_snapshot = await self.documents.obtener_contexto_reciente_seguro(conversation.id)
        previous = self._analizar_resumen_anterior(
            previous_snapshot.summary if previous_snapshot else conversation.summary
        )
        actions = self.repository.listar_acciones(project_id, "proposed", 100)
        summary = self._resumen_determinista(previous, completed, actions, target_sequence)
        self.db.rollback()
        locked = self.repository.obtener_conversacion(project_id, conversation.id, for_update=True)
        if locked is None or locked.summary_until_sequence != initial_boundary:
            self.db.rollback()
            return None
        serialized_summary = json.dumps(
            sanear_datos_contexto(summary.model_dump(mode="json")),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        document = documento_instantanea_contexto(
            locked,
            summary=serialized_summary,
            context=sanear_datos_contexto(summary.model_dump(mode="json")),
            until_sequence=target_sequence,
        )
        await self.documents.guardar_o_actualizar_contexto(document)
        locked.summary = None
        locked.summary_until_sequence = target_sequence
        self.db.commit()
        return summary, conversation_id

    @staticmethod
    def _analizar_resumen_anterior(raw: str | None) -> ResumenMemoriaConversacion | None:
        if not raw:
            return None
        try:
            return ResumenMemoriaConversacion.model_validate_json(raw)
        except ValueError:
            return None

    @staticmethod
    def _resumen_determinista(previous, messages, actions, target_sequence):
        user_messages = [item for item in messages if item.role == "user"]
        project_goal = previous.project_goal if previous else ""
        if not project_goal and user_messages:
            project_goal = sanear_texto_no_confiable(user_messages[0].content, 1000)
        decisions = list(previous.decisions if previous else [])
        questions = list(previous.open_questions if previous else [])
        changes = list(previous.recent_changes if previous else [])
        entities = list(previous.important_entities if previous else [])
        for message in messages:
            clean = sanear_texto_no_confiable(message.content, 1000)
            normalized = clean.casefold()
            if any(marker in normalized for marker in ("decid", "acord", "usaremos", "se define")):
                decisions.append(clean)
            if "?" in clean and message.role == "user":
                questions.append(clean)
            if any(
                intent in message.detected_intents for intent in ("modify_uml", "specify_method")
            ):
                changes.append(clean)
            for reference in message.references_json:
                label = str(reference.get("label") or "").strip()
                if label:
                    entities.append(label)
        return ResumenMemoriaConversacion(
            project_goal=project_goal,
            decisions=_cola_unica(decisions, 50),
            open_questions=_cola_unica(questions, 50),
            recent_changes=_cola_unica(changes, 50),
            important_entities=_cola_unica(entities, 100),
            pending_actions=[f"{item.action_type}:{item.id}" for item in actions],
            member_preferences_relevant_to_work=list(
                previous.member_preferences_relevant_to_work if previous else []
            ),
            summary_until_sequence=target_sequence,
        )


def _cola_unica(values: list[str], limit: int) -> list[str]:
    unique: dict[str, str] = {}
    for value in values:
        clean = value.strip()
        if clean:
            unique[clean.casefold()] = clean
    return list(unique.values())[-limit:]


async def resumir_conversacion_proyecto(
    project_id: UUID, user_id: UUID, conversation_id: UUID | None = None
) -> None:
    try:
        with SessionLocal() as db:
            result = await ServicioMemoriaConversacion(db).resumir_si_es_necesario(
                project_id, user_id, conversation_id, force=True
            )
        if result is None:
            return
        summary, _ = result
        await PublicadorEventosIAProyecto().publicar_persistido(
            project_id=project_id,
            actor_user_id=user_id,
            event_type="AI_CONVERSATION_SUMMARY_UPDATED",
            payload={"summary_until_sequence": summary.summary_until_sequence},
            correlation_id=uuid4(),
            conversation_sequence=summary.summary_until_sequence,
        )
    except Exception:
        logger.exception("No se pudo actualizar la memoria resumida del proyecto")
