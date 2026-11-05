from app.core.config.configuracion import settings
from app.core.database.sesion import SessionLocal
from app.modules.notificaciones.services import DistribuidorBandejaSalidaNotificaciones


def main() -> None:
    with SessionLocal() as db:
        result = DistribuidorBandejaSalidaNotificaciones(db).dispatch(settings.notification_outbox_batch_size)
    print(
        "notification-outbox "
        f"processed={result['processed']} delivered={result['delivered']} "
        f"retry={result['retry']} dead={result['dead']}"
    )


if __name__ == "__main__":
    main()
