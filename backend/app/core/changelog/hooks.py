"""Hooks de SQLAlchemy para captura de eventos del registro de cambios (NoSQL/Redis)."""

import logging

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.changelog.contracts import PendingChange

logger = logging.getLogger(__name__)
_installed: bool = False


def install_change_log_hooks() -> None:
    """Instala los listeners after_commit y after_rollback en Session (idempotente)."""
    global _installed
    if _installed:
        return
    _installed = True
    event.listen(Session, "after_commit", flush_pending_changes)
    event.listen(Session, "after_rollback", clear_pending_changes)


def queue_change(db: Session, entry: PendingChange) -> None:
    """Encola un cambio pendiente en la sesión para ser enviado tras el commit."""
    pending = db.info.setdefault("change_log_pending", [])
    pending.append(entry)


def flush_pending_changes(session: Session) -> None:
    """Vacía los cambios pendientes hacia Redis Streams."""
    changes: list[PendingChange] = session.info.pop("change_log_pending", [])
    if not changes:
        return
    try:
        from app.core.changelog.service import ChangeLogService
        ChangeLogService().append_many(changes)
    except Exception as exc:
        logger.warning("Error al volcar cambios a Redis Streams: %s", exc)


def clear_pending_changes(session: Session) -> None:
    """Descarta cambios pendientes tras un rollback."""
    session.info.pop("change_log_pending", None)
