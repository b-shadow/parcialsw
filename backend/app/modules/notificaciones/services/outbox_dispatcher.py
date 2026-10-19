from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.notificaciones.models import Notification, NotificationOutbox
from app.modules.notificaciones.services.push_service import PushNotificationService


class NotificationOutboxDispatcher:
    MAX_ATTEMPTS = 6
    LOCK_TIMEOUT = timedelta(minutes=5)

    def __init__(self, db: Session) -> None:
        self.db = db

    def dispatch(self, limit: int = 50) -> dict[str, int]:
        now = datetime.now(UTC)
        worker = str(uuid4())
        jobs = list(self.db.scalars(
            select(NotificationOutbox).where(
                NotificationOutbox.available_at <= now,
                or_(
                    NotificationOutbox.status.in_(("pending", "retry")),
                    (NotificationOutbox.status == "processing")
                    & (NotificationOutbox.locked_at < now - self.LOCK_TIMEOUT),
                ),
            ).order_by(NotificationOutbox.available_at).limit(max(1, min(limit, 200)))
            .with_for_update(skip_locked=True)
        ))
        for job in jobs:
            job.status = "processing"
            job.locked_at = now
            job.locked_by = worker
        self.db.commit()

        result = {"processed": 0, "delivered": 0, "retry": 0, "dead": 0}
        for job in jobs:
            result["processed"] += 1
            notification = self.db.get(Notification, job.notification_id)
            try:
                if notification is None:
                    raise ValueError("notification_missing")
                delivery = PushNotificationService(self.db).send_to_users(
                    {notification.recipient_user_id},
                    {
                        "notification_id": str(notification.id),
                        "title": notification.title,
                        "body": notification.body,
                        "tag": notification.dedup_key,
                        "deep_link": notification.deep_link,
                    },
                )
                if delivery["failed"]:
                    raise OSError("push_temporarily_failed")
                job.status = "delivered"
                job.delivered_at = datetime.now(UTC)
                job.last_error_code = None
                result["delivered"] += 1
            except (OSError, ValueError) as exc:
                job.attempt_count += 1
                job.last_error_code = str(exc)[:120]
                if job.attempt_count >= self.MAX_ATTEMPTS:
                    job.status = "dead"
                    result["dead"] += 1
                else:
                    job.status = "retry"
                    delay = min(3600, 2 ** job.attempt_count * 30) + random.randint(0, 15)
                    job.available_at = datetime.now(UTC) + timedelta(seconds=delay)
                    result["retry"] += 1
            finally:
                job.locked_at = None
                job.locked_by = None
                self.db.commit()
        return result
