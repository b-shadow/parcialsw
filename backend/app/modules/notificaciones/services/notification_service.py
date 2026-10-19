from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.notificaciones.models import (
    Notification,
    NotificationOutbox,
    NotificationPreference,
)
from app.modules.notificaciones.schemas.notification import NotificationDeepLink


@dataclass(frozen=True)
class DomainNotificationEvent:
    type: str
    category: str
    title: str
    body: str
    recipient_user_ids: set[UUID]
    dedup_entity_id: UUID | str
    project_id: UUID | None = None
    actor_user_id: UUID | None = None
    severity: str = "info"
    resource_type: str | None = None
    resource_id: UUID | None = None
    deep_link: NotificationDeepLink = field(
        default_factory=lambda: NotificationDeepLink(route_name="projects")
    )
    push_default: bool = True
    group_key: str | None = None
    exclude_actor: bool = True


class NotificationService:
    """Records the durable inbox and outbox in the caller's transaction."""

    MANDATORY_IN_APP: ClassVar[frozenset[str]] = frozenset({"access", "security"})

    def __init__(self, db: Session) -> None:
        self.db = db

    def record(self, event: DomainNotificationEvent) -> list[Notification]:
        created: list[Notification] = []
        now = datetime.now(UTC)
        for recipient_id in sorted(event.recipient_user_ids, key=str):
            if event.exclude_actor and event.actor_user_id == recipient_id:
                continue
            preference = self._preference(recipient_id, event.category, event.project_id)
            in_app = event.category in self.MANDATORY_IN_APP or preference is None or preference.in_app_enabled
            if preference and preference.muted_until and preference.muted_until > now:
                in_app = event.category in self.MANDATORY_IN_APP
            if not in_app:
                continue
            dedup_key = f"{event.type}:{event.dedup_entity_id}:{recipient_id}"
            existing = self.db.scalar(
                select(Notification).where(
                    Notification.recipient_user_id == recipient_id,
                    Notification.dedup_key == dedup_key,
                )
            )
            if existing:
                created.append(existing)
                continue
            notification = Notification(
                recipient_user_id=recipient_id,
                project_id=event.project_id,
                actor_user_id=event.actor_user_id,
                type=event.type,
                severity=event.severity,
                title=event.title[:180],
                body=event.body[:500],
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                deep_link=event.deep_link.model_dump(mode="json"),
                dedup_key=dedup_key,
                group_key=event.group_key,
                occurred_at=now,
            )
            self.db.add(notification)
            self.db.flush()
            push_enabled = event.push_default and (preference is None or preference.push_enabled)
            if push_enabled and not (preference and preference.muted_until and preference.muted_until > now):
                self.db.add(
                    NotificationOutbox(
                        notification_id=notification.id,
                        channel="web_push",
                        status="pending",
                        available_at=now,
                    )
                )
            created.append(notification)
        return created

    def list_for_user(
        self, user_id: UUID, *, cursor: UUID | None, limit: int, unread_only: bool
    ) -> tuple[list[Notification], bool]:
        safe_limit = max(1, min(limit, 100))
        statement = select(Notification).where(
            Notification.recipient_user_id == user_id,
            Notification.archived_at.is_(None),
        )
        if unread_only:
            statement = statement.where(Notification.read_at.is_(None))
        if cursor:
            pivot = self.db.get(Notification, cursor)
            if pivot and pivot.recipient_user_id == user_id:
                statement = statement.where(
                    or_(
                        Notification.occurred_at < pivot.occurred_at,
                        (Notification.occurred_at == pivot.occurred_at) & (Notification.id < pivot.id),
                    )
                )
        rows = list(
            self.db.scalars(
                statement.order_by(Notification.occurred_at.desc(), Notification.id.desc())
                .limit(safe_limit + 1)
            )
        )
        return rows[:safe_limit], len(rows) > safe_limit

    def unread_count(self, user_id: UUID) -> int:
        return int(self.db.scalar(select(func.count(Notification.id)).where(
            Notification.recipient_user_id == user_id,
            Notification.read_at.is_(None),
            Notification.archived_at.is_(None),
        )) or 0)

    def mark_read(self, notification_id: UUID, user_id: UUID, *, clicked: bool = False) -> Notification:
        notification = self.db.scalar(select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_user_id == user_id,
        ))
        if notification is None:
            raise LookupError("NOTIFICATION_NOT_FOUND")
        now = datetime.now(UTC)
        notification.read_at = notification.read_at or now
        if clicked:
            notification.clicked_at = notification.clicked_at or now
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_read(self, user_id: UUID, *, before: datetime | None = None) -> int:
        now = datetime.now(UTC)
        statement = select(Notification).where(
            Notification.recipient_user_id == user_id,
            Notification.read_at.is_(None),
            Notification.occurred_at <= (before or now),
        )
        rows = list(self.db.scalars(statement))
        for item in rows:
            item.read_at = now
        self.db.commit()
        return len(rows)

    def preferences(self, user_id: UUID) -> list[NotificationPreference]:
        return list(self.db.scalars(select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        ).order_by(NotificationPreference.category)))

    def replace_preferences(self, user_id: UUID, items: list[dict]) -> list[NotificationPreference]:
        existing = {(item.project_id, item.category): item for item in self.preferences(user_id)}
        for value in items:
            key = (value.get("project_id"), value["category"])
            preference = existing.get(key)
            if preference is None:
                preference = NotificationPreference(user_id=user_id, **value)
                self.db.add(preference)
            else:
                preference.in_app_enabled = value["in_app_enabled"]
                preference.push_enabled = value["push_enabled"]
                preference.muted_until = value.get("muted_until")
        self.db.commit()
        return self.preferences(user_id)

    def _preference(
        self, user_id: UUID, category: str, project_id: UUID | None
    ) -> NotificationPreference | None:
        preferences = list(self.db.scalars(select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.category == category,
            or_(
                NotificationPreference.project_id == project_id,
                NotificationPreference.project_id.is_(None),
            ),
        )))
        return next((item for item in preferences if item.project_id == project_id), None) or next(
            (item for item in preferences if item.project_id is None), None
        )
