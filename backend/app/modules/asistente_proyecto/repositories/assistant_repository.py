from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import User
from app.modules.asistente_proyecto.models import (
    AiAction,
    AiConversation,
    AiMessage,
    AiProjectSettings,
    AiRecommendation,
)


class AssistantRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_settings(self, project_id: UUID) -> AiProjectSettings | None:
        return self.db.scalar(select(AiProjectSettings).where(AiProjectSettings.project_id == project_id))

    def get_conversation(
        self, project_id: UUID, conversation_id: UUID | None = None, for_update: bool = False
    ) -> AiConversation | None:
        statement = select(AiConversation).where(AiConversation.project_id == project_id)
        if conversation_id is not None:
            statement = statement.where(AiConversation.id == conversation_id)
        else:
            statement = statement.order_by(AiConversation.updated_at.desc())
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def list_conversations(self, project_id: UUID) -> list[AiConversation]:
        return list(
            self.db.scalars(
                select(AiConversation)
                .where(AiConversation.project_id == project_id)
                .order_by(AiConversation.updated_at.desc())
            )
        )

    def get_message_by_client_id(
        self, conversation_id: UUID, author_user_id: UUID, client_message_id: UUID
    ) -> AiMessage | None:
        return self.db.scalar(
            select(AiMessage).where(
                AiMessage.conversation_id == conversation_id,
                AiMessage.author_user_id == author_user_id,
                AiMessage.client_message_id == client_message_id,
            )
        )

    def get_assistant_message_by_correlation(
        self, conversation_id: UUID, correlation_id: UUID
    ) -> AiMessage | None:
        return self.db.scalar(
            select(AiMessage).where(
                AiMessage.conversation_id == conversation_id,
                AiMessage.correlation_id == correlation_id,
                AiMessage.role == "assistant",
            )
        )

    def list_messages(
        self,
        conversation_id: UUID,
        *,
        before_sequence: int | None,
        after_sequence: int | None,
        limit: int,
    ) -> list[AiMessage]:
        statement = select(AiMessage).where(AiMessage.conversation_id == conversation_id)
        if before_sequence is not None:
            statement = statement.where(AiMessage.sequence_number < before_sequence)
        if after_sequence is not None:
            statement = statement.where(AiMessage.sequence_number > after_sequence)
        if after_sequence is not None:
            statement = statement.order_by(AiMessage.sequence_number).limit(limit)
            return list(self.db.scalars(statement))
        statement = statement.order_by(AiMessage.sequence_number.desc()).limit(limit)
        return list(reversed(list(self.db.scalars(statement))))

    def message_exists_before(self, conversation_id: UUID, sequence: int) -> bool:
        return self.db.scalar(
            select(AiMessage.id).where(
                AiMessage.conversation_id == conversation_id,
                AiMessage.sequence_number < sequence,
            ).limit(1)
        ) is not None

    def message_exists_after(self, conversation_id: UUID, sequence: int) -> bool:
        return self.db.scalar(
            select(AiMessage.id).where(
                AiMessage.conversation_id == conversation_id,
                AiMessage.sequence_number > sequence,
            ).limit(1)
        ) is not None

    def user_display_names(self, user_ids: set[UUID]) -> dict[UUID, str]:
        if not user_ids:
            return {}
        users = self.db.scalars(select(User).where(User.id.in_(user_ids)))
        return {user.id: user.full_name or user.email for user in users}

    def list_actions(
        self, project_id: UUID, status: str | None, limit: int,
        conversation_id: UUID | None = None,
    ) -> list[AiAction]:
        statement = select(AiAction).where(AiAction.project_id == project_id)
        if conversation_id is not None:
            statement = statement.where(AiAction.conversation_id == conversation_id)
        if status:
            statement = statement.where(AiAction.status == status)
        return list(self.db.scalars(statement.order_by(AiAction.created_at.desc()).limit(limit)))

    def get_action(
        self, project_id: UUID, action_id: UUID, *, for_update: bool = False
    ) -> AiAction | None:
        statement = select(AiAction).where(
            AiAction.project_id == project_id, AiAction.id == action_id
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def get_action_by_idempotency(self, project_id: UUID, key: UUID) -> AiAction | None:
        return self.db.scalar(
            select(AiAction).where(
                AiAction.project_id == project_id,
                AiAction.idempotency_key == key,
            )
        )

    def list_actions_for_message(self, message_id: UUID) -> list[AiAction]:
        return list(
            self.db.scalars(
                select(AiAction)
                .where(AiAction.source_message_id == message_id)
                .order_by(AiAction.created_at)
            )
        )

    def list_recommendations_for_message(self, message_id: UUID) -> list[AiRecommendation]:
        return list(
            self.db.scalars(
                select(AiRecommendation)
                .where(AiRecommendation.source_message_id == message_id)
                .order_by(AiRecommendation.created_at)
            )
        )

    def list_recommendations(
        self, project_id: UUID, status: str | None, severity: str | None, limit: int,
        conversation_id: UUID | None = None,
    ) -> list[AiRecommendation]:
        statement = select(AiRecommendation).where(AiRecommendation.project_id == project_id)
        if conversation_id is not None:
            statement = statement.where(AiRecommendation.conversation_id == conversation_id)
        if status:
            statement = statement.where(AiRecommendation.status == status)
        if severity:
            statement = statement.where(AiRecommendation.severity == severity)
        return list(
            self.db.scalars(statement.order_by(AiRecommendation.created_at.desc()).limit(limit))
        )

    def get_recommendation(
        self, project_id: UUID, recommendation_id: UUID, *, for_update: bool = False
    ) -> AiRecommendation | None:
        statement = select(AiRecommendation).where(
            AiRecommendation.project_id == project_id,
            AiRecommendation.id == recommendation_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)
