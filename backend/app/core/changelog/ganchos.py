"""Hooks de SQLAlchemy para captura de eventos del registro de cambios (NoSQL/Redis)."""

import logging

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.changelog.contratos import CambioPendiente

logger = logging.getLogger(__name__)
_installed: bool = False


def instalar_ganchos_registro_cambios() -> None:
    """Instala los listeners after_commit y after_rollback en Session (idempotente)."""
    global _installed
    if _installed:
        return
    _installed = True
    event.listen(Session, "after_commit", vaciar_cambios_pendientes)
    event.listen(Session, "after_rollback", limpiar_cambios_pendientes)


def encolar_cambio(db: Session, entry: CambioPendiente) -> None:
    """Encola un cambio pendiente en la sesión para ser enviado tras el commit."""
    pending = db.info.setdefault("change_log_pending", [])
    pending.append(entry)


def vaciar_cambios_pendientes(session: Session) -> None:
    """Vacía los cambios pendientes hacia Redis Streams."""
    changes: list[CambioPendiente] = session.info.pop("change_log_pending", [])
    if not changes:
        return
    try:
        from app.core.changelog.servicio import ServicioRegistroCambios
        ServicioRegistroCambios().append_many(changes)
    except Exception as exc:
        logger.warning("Error al volcar cambios a Redis Streams: %s", exc)


def limpiar_cambios_pendientes(session: Session) -> None:
    """Descarta cambios pendientes tras un rollback."""
    session.info.pop("change_log_pending", None)
