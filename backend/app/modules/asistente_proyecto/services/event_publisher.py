import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select

from app.core.database.session import SessionLocal
from app.modules.acceso_usuarios.repositories.user_repository import UserRepository
from app.modules.notificaciones.schemas.notification import NotificationDeepLink
from app.modules.notificaciones.services import DomainNotificationEvent, NotificationService
from app.modules.proyectos_colaboracion.models import ProjectMember
from app.modules.proyectos_colaboracion.services.project_service import ProjectService
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)


class ProjectAiEventPublisher:
    """Persiste eventos antes de emitirlos; un fallo de socket no revierte negocio."""

    async def publish_persisted(
        self,
        *,
        project_id: UUID,
        actor_user_id: UUID,
        event_type: str,
        payload: dict,
        correlation_id: UUID,
        diagram_id: UUID | None = None,
        conversation_sequence: int | None = None,
    ) -> dict:
        with SessionLocal() as db:
            actor = UserRepository(db).get_by_id(actor_user_id)
            actor_name = actor.full_name if actor else "Usuario"
            event, _ = ProjectService(db).record_collaboration_event(
                project_id=project_id,
                diagram_id=diagram_id,
                user_id=actor_user_id,
                client_event_id=uuid4(),
                event_type=event_type,
                element_type=None,
                element_id=None,
                base_version=None,
                payload={
                    **payload,
                    "correlation_id": str(correlation_id),
                    "conversation_sequence": conversation_sequence,
                },
            )
        envelope = self._envelope(
            project_id=project_id,
            actor_user_id=actor_user_id,
            actor_name=actor_name,
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            sequence_number=event.sequence_number,
            conversation_sequence=conversation_sequence,
            event_id=event.id,
            persistent=True,
        )
        try:
            await manager.broadcast(str(project_id), envelope)
        except Exception:
            logger.exception("No se pudo difundir evento IA persistido")
        try:
            await self._push_if_relevant(event_type, payload, project_id, actor_user_id)
        except Exception:
            logger.exception("No se pudo enviar la notificacion push del evento IA")
        return envelope

    async def publish_ephemeral(
        self,
        *,
        project_id: UUID,
        actor_user_id: UUID,
        actor_name: str,
        event_type: str,
        payload: dict,
        correlation_id: UUID,
        conversation_sequence: int | None = None,
    ) -> dict:
        envelope = self._envelope(
            project_id=project_id,
            actor_user_id=actor_user_id,
            actor_name=actor_name,
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
            diagram_id=None,
            sequence_number=0,
            conversation_sequence=conversation_sequence,
            event_id=uuid4(),
            persistent=False,
        )
        await manager.broadcast(str(project_id), envelope)
        return envelope

    @staticmethod
    def _envelope(**values) -> dict:
        return {
            "protocol_version": 2,
            "type": values["event_type"],
            "event_id": str(values["event_id"]),
            "project_id": str(values["project_id"]),
            "diagram_id": str(values["diagram_id"]) if values["diagram_id"] else None,
            "sequence_number": values["sequence_number"],
            "conversation_sequence": values["conversation_sequence"],
            "correlation_id": str(values["correlation_id"]),
            "occurred_at": datetime.now(UTC).isoformat(),
            "persistent": values["persistent"],
            "actor": {
                "user_id": str(values["actor_user_id"]),
                "display_name": values["actor_name"],
            },
            "payload": values["payload"],
        }

    @staticmethod
    async def _push_if_relevant(
        event_type: str, payload: dict, project_id: UUID, actor_user_id: UUID
    ) -> None:
        is_high_action = (
            event_type == "AI_ACTION_PROPOSED" and payload.get("risk_level") == "high"
        )
        is_critical = (
            event_type == "AI_RECOMMENDATION_CREATED"
            and payload.get("severity") == "critical"
        )
        is_applied = (
            event_type == "AI_ACTION_STATUS_CHANGED" and payload.get("status") == "applied"
        )
        if not (is_high_action or is_critical or is_applied):
            return
        with SessionLocal() as db:
            recipients = set(db.scalars(select(ProjectMember.user_id).where(
                ProjectMember.project_id == project_id
            )))
            notification_id = payload.get("action_id") or payload.get("recommendation_id") or uuid4()
            NotificationService(db).record(DomainNotificationEvent(
                type=event_type, category="ai", title="Actividad de IA en el proyecto",
                body=str(payload.get("title") or payload.get("description") or "Hay una actualizacion relevante."),
                recipient_user_ids=recipients, dedup_entity_id=notification_id,
                project_id=project_id, actor_user_id=actor_user_id,
                deep_link=NotificationDeepLink(
                    route_name="project_ai", params={"project_id": str(project_id)}
                ), push_default=is_high_action or is_critical,
            ))
            db.commit()
