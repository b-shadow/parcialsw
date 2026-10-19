import json
import logging
from uuid import UUID, uuid4

from ai_engine.context.sanitizer import sanitize_context_data, sanitize_untrusted_text
from pydantic import BaseModel, Field

from app.core.database.session import SessionLocal
from app.modules.asistente_proyecto.repositories.assistant_repository import AssistantRepository
from app.modules.asistente_proyecto.services.assistant_service import AssistantContractService
from app.modules.asistente_proyecto.services.event_publisher import ProjectAiEventPublisher

logger = logging.getLogger(__name__)


class ConversationMemorySummary(BaseModel):
    project_goal: str = Field(default="", max_length=1000)
    decisions: list[str] = Field(default_factory=list, max_length=50)
    open_questions: list[str] = Field(default_factory=list, max_length=50)
    recent_changes: list[str] = Field(default_factory=list, max_length=50)
    important_entities: list[str] = Field(default_factory=list, max_length=100)
    pending_actions: list[str] = Field(default_factory=list, max_length=100)
    member_preferences_relevant_to_work: list[str] = Field(default_factory=list, max_length=30)
    summary_until_sequence: int = Field(ge=0)


class ConversationMemoryService:
    def __init__(self, db) -> None:
        self.db = db
        self.repository = AssistantRepository(db)

    def summarize_if_needed(
        self, project_id: UUID, user_id: UUID,
        conversation_id: UUID | None = None, *, force: bool = False,
    ) -> tuple[ConversationMemorySummary, UUID] | None:
        contracts = AssistantContractService(self.db)
        settings = contracts.get_settings(project_id, user_id)
        conversation = contracts.get_conversation(project_id, user_id, conversation_id)
        unsummarized = conversation.last_message_sequence - conversation.summary_until_sequence
        if unsummarized <= 0 or (
            not force and unsummarized < settings.summary_trigger_messages
        ):
            return None
        initial_boundary = conversation.summary_until_sequence
        messages = self.repository.list_messages(
            conversation.id,
            before_sequence=None,
            after_sequence=initial_boundary,
            limit=min(settings.summary_trigger_messages * 2, 200),
        )
        completed = [item for item in messages if item.status == "completed"]
        if not completed or (
            not force and len(completed) < settings.summary_trigger_messages
        ):
            return None
        target_sequence = completed[-1].sequence_number
        conversation_id = conversation.id
        previous = self._parse_previous(conversation.summary)
        actions = self.repository.list_actions(project_id, "proposed", 100)
        summary = self._deterministic_summary(previous, completed, actions, target_sequence)
        self.db.rollback()
        locked = self.repository.get_conversation(
            project_id, conversation.id, for_update=True
        )
        if locked is None or locked.summary_until_sequence != initial_boundary:
            self.db.rollback()
            return None
        locked.summary = json.dumps(
            sanitize_context_data(summary.model_dump(mode="json")),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        locked.summary_until_sequence = target_sequence
        self.db.commit()
        return summary, conversation_id

    @staticmethod
    def _parse_previous(raw: str | None) -> ConversationMemorySummary | None:
        if not raw:
            return None
        try:
            return ConversationMemorySummary.model_validate_json(raw)
        except ValueError:
            return None

    @staticmethod
    def _deterministic_summary(previous, messages, actions, target_sequence):
        user_messages = [item for item in messages if item.role == "user"]
        project_goal = previous.project_goal if previous else ""
        if not project_goal and user_messages:
            project_goal = sanitize_untrusted_text(user_messages[0].content, 1000)
        decisions = list(previous.decisions if previous else [])
        questions = list(previous.open_questions if previous else [])
        changes = list(previous.recent_changes if previous else [])
        entities = list(previous.important_entities if previous else [])
        for message in messages:
            clean = sanitize_untrusted_text(message.content, 1000)
            normalized = clean.casefold()
            if any(marker in normalized for marker in ("decid", "acord", "usaremos", "se define")):
                decisions.append(clean)
            if "?" in clean and message.role == "user":
                questions.append(clean)
            if any(intent in message.detected_intents for intent in ("modify_uml", "specify_method")):
                changes.append(clean)
            for reference in message.references_json:
                label = str(reference.get("label") or "").strip()
                if label:
                    entities.append(label)
        return ConversationMemorySummary(
            project_goal=project_goal,
            decisions=_unique_tail(decisions, 50),
            open_questions=_unique_tail(questions, 50),
            recent_changes=_unique_tail(changes, 50),
            important_entities=_unique_tail(entities, 100),
            pending_actions=[f"{item.action_type}:{item.id}" for item in actions],
            member_preferences_relevant_to_work=list(
                previous.member_preferences_relevant_to_work if previous else []
            ),
            summary_until_sequence=target_sequence,
        )


def _unique_tail(values: list[str], limit: int) -> list[str]:
    unique: dict[str, str] = {}
    for value in values:
        clean = value.strip()
        if clean:
            unique[clean.casefold()] = clean
    return list(unique.values())[-limit:]


async def summarize_project_conversation(
    project_id: UUID, user_id: UUID, conversation_id: UUID | None = None
) -> None:
    try:
        with SessionLocal() as db:
            result = ConversationMemoryService(db).summarize_if_needed(
                project_id, user_id, conversation_id, force=True
            )
        if result is None:
            return
        summary, _ = result
        await ProjectAiEventPublisher().publish_persisted(
            project_id=project_id,
            actor_user_id=user_id,
            event_type="AI_CONVERSATION_SUMMARY_UPDATED",
            payload={"summary_until_sequence": summary.summary_until_sequence},
            correlation_id=uuid4(),
            conversation_sequence=summary.summary_until_sequence,
        )
    except Exception:
        logger.exception("No se pudo actualizar la memoria resumida del proyecto")
