from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.modules.notificaciones.services import NotificationOutboxDispatcher


def main() -> None:
    with SessionLocal() as db:
        result = NotificationOutboxDispatcher(db).dispatch(settings.notification_outbox_batch_size)
    print(
        "notification-outbox "
        f"processed={result['processed']} delivered={result['delivered']} "
        f"retry={result['retry']} dead={result['dead']}"
    )


if __name__ == "__main__":
    main()
