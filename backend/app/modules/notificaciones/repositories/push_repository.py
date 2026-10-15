from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notificaciones.models import PushSubscription


class PushRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_endpoint(self, endpoint: str) -> PushSubscription | None:
        return self.db.scalar(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )

    def list_active_for_users(self, user_ids: set[UUID]) -> list[PushSubscription]:
        if not user_ids:
            return []
        return list(
            self.db.scalars(
                select(PushSubscription).where(
                    PushSubscription.user_id.in_(user_ids),
                    PushSubscription.is_active.is_(True),
                )
            )
        )

    def delete(self, subscription: PushSubscription) -> None:
        self.db.delete(subscription)
