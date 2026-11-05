from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notificaciones.models import SuscripcionPush


class RepositorioPush:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obtener_por_endpoint(self, endpoint: str) -> SuscripcionPush | None:
        return self.db.scalar(
            select(SuscripcionPush).where(SuscripcionPush.endpoint == endpoint)
        )

    def listar_activas_para_usuarios(self, user_ids: set[UUID]) -> list[SuscripcionPush]:
        if not user_ids:
            return []
        return list(
            self.db.scalars(
                select(SuscripcionPush).where(
                    SuscripcionPush.user_id.in_(user_ids),
                    SuscripcionPush.is_active.is_(True),
                )
            )
        )

    def delete(self, subscription: SuscripcionPush) -> None:
        self.db.delete(subscription)
