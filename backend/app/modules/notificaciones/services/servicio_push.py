import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.core.database.sesion import SessionLocal
from app.modules.notificaciones.models import SuscripcionPush
from app.modules.notificaciones.repositories import RepositorioPush
from app.modules.notificaciones.schemas import CreacionSuscripcionPush
from app.modules.proyectos_colaboracion.models import IntegranteProyecto

logger = logging.getLogger(__name__)


class ServicioNotificacionesPush:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.subscriptions = RepositorioPush(db)

    @property
    def enabled(self) -> bool:
        return bool(
            settings.vapid_public_key
            and settings.vapid_private_key
            and settings.vapid_subject
        )

    def suscribir(
        self,
        user_id: UUID,
        payload: CreacionSuscripcionPush,
        user_agent: str | None,
    ) -> SuscripcionPush:
        endpoint = str(payload.endpoint)
        subscription = self.subscriptions.obtener_por_endpoint(endpoint)
        if subscription is None:
            subscription = SuscripcionPush(user_id=user_id, endpoint=endpoint)
            self.db.add(subscription)
        subscription.user_id = user_id
        subscription.p256dh = payload.keys.p256dh
        subscription.auth = payload.keys.auth
        subscription.expires_at = payload.expiration_time
        subscription.user_agent = user_agent[:512] if user_agent else None
        subscription.content_encoding = "aes128gcm"
        subscription.is_active = True
        subscription.failure_count = 0
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def cancelar_suscripcion(self, user_id: UUID, endpoint: str) -> bool:
        subscription = self.subscriptions.obtener_por_endpoint(endpoint)
        if subscription is None or subscription.user_id != user_id:
            return False
        self.subscriptions.delete(subscription)
        self.db.commit()
        return True

    def enviar_a_usuarios(self, user_ids: set[UUID], payload: dict) -> dict[str, int]:
        result = {"sent": 0, "failed": 0, "removed": 0}
        if not self.enabled:
            return result
        data = json.dumps(payload, ensure_ascii=False)
        now = datetime.now(UTC)
        for subscription in self.subscriptions.listar_activas_para_usuarios(user_ids):
            if subscription.expires_at and subscription.expires_at <= now:
                self.subscriptions.delete(subscription)
                result["removed"] += 1
                continue
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                    },
                    data=data,
                    vapid_private_key=settings.vapid_private_key,
                    vapid_claims={"sub": settings.vapid_subject},
                    ttl=300,
                )
                subscription.last_success_at = now
                subscription.failure_count = 0
                result["sent"] += 1
            except WebPushException as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code in {404, 410}:
                    self.subscriptions.delete(subscription)
                    result["removed"] += 1
                else:
                    subscription.failure_count += 1
                    subscription.is_active = subscription.failure_count < 5
                    result["failed"] += 1
                    logger.warning("Web Push fallo para una suscripcion: status=%s", status_code)
            except (OSError, ValueError) as exc:
                subscription.failure_count += 1
                subscription.is_active = subscription.failure_count < 5
                result["failed"] += 1
                logger.warning("No se pudo preparar Web Push: %s", exc)
        self.db.commit()
        return result


def enviar_push_usuario(user_id: UUID | str, payload: dict) -> dict[str, int]:
    with SessionLocal() as db:
        return ServicioNotificacionesPush(db).enviar_a_usuarios({UUID(str(user_id))}, payload)


def enviar_push_proyecto(
    project_id: UUID | str,
    payload: dict,
    excluded_user_id: UUID | str | None = None,
) -> dict[str, int]:
    project_uuid = UUID(str(project_id))
    excluded_uuid = UUID(str(excluded_user_id)) if excluded_user_id else None
    with SessionLocal() as db:
        user_ids = set(
            db.scalars(
                select(IntegranteProyecto.user_id).where(IntegranteProyecto.project_id == project_uuid)
            )
        )
        if excluded_uuid:
            user_ids.discard(excluded_uuid)
        return ServicioNotificacionesPush(db).enviar_a_usuarios(user_ids, payload)
