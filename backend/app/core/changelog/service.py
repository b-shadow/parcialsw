"""Servicio del registro de cambios en NoSQL (Redis Streams) con respaldo en PostgreSQL."""

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.changelog.contracts import (
    ChangeLogEntry,
    ChangeLogPage,
    PendingChange,
    build_summary,
)
from app.core.config.settings import settings
from app.core.redis.client import get_redis, redis_key, redis_status
from app.modules.acceso_usuarios.models import AuditLog, User
from app.modules.acceso_usuarios.services.audit_service import sanitize_audit_metadata

logger = logging.getLogger(__name__)


def queue_change(db: Session, change: PendingChange) -> None:
    """Función de conveniencia a nivel de módulo para encolar cambios."""
    pending = db.info.setdefault("change_log_pending", [])
    pending.append(change)


class ChangeLogService:
    def append_many(self, changes: list[PendingChange]) -> int:
        client = get_redis()
        if client is None:
            return 0

        written = 0
        try:
            pipe = client.pipeline()
            for change in changes:
                sanitized_meta = sanitize_audit_metadata(change.metadata or {})
                meta_str = json.dumps(sanitized_meta, default=str)[:2048]
                summary = build_summary(change.action, change.metadata)

                payload = {
                    "project_id": str(change.project_id),
                    "occurred_at": datetime.now(UTC).isoformat(),
                    "actor_user_id": str(change.actor_user_id) if change.actor_user_id else "",
                    "source": change.source,
                    "module": change.module,
                    "action": change.action,
                    "entity_type": change.entity_type or "",
                    "entity_id": str(change.entity_id) if change.entity_id else "",
                    "diagram_id": str(change.diagram_id) if change.diagram_id else "",
                    "summary": summary,
                    "metadata": meta_str,
                }

                p_key = redis_key("changelog", "project", str(change.project_id))
                g_key = redis_key("changelog", "all")

                pipe.xadd(
                    p_key,
                    payload,
                    maxlen=settings.redis_change_log_maxlen,
                    approximate=True,
                )
                pipe.xadd(
                    g_key,
                    payload,
                    maxlen=50000,
                    approximate=True,
                )
                written += 1
            pipe.execute()
        except Exception as exc:
            logger.warning("Fallo al escribir en Redis Streams: %s", exc)
        return written

    def list_project(
        self,
        project_id: UUID,
        *,
        db: Session | None = None,
        before_id: str | None = None,
        limit: int = 50,
        actor_id: UUID | None = None,
        entity_type: str | None = None,
    ) -> ChangeLogPage:
        limit = max(1, min(limit, 100))

        if redis_status() != "available":
            return self._fallback_from_db(
                project_id, db=db, before_id=before_id, limit=limit, actor_id=actor_id, entity_type=entity_type
            )

        client = get_redis()
        if client is None:
            return self._fallback_from_db(
                project_id, db=db, before_id=before_id, limit=limit, actor_id=actor_id, entity_type=entity_type
            )

        stream_key = redis_key("changelog", "project", str(project_id))
        max_id = before_id or "+"

        try:
            count = min(limit * 5 + 1, 500)
            raw_entries = client.xrevrange(stream_key, max=max_id, min="-", count=count)
        except Exception as exc:
            logger.warning("Error leyendo Redis Stream: %s", exc)
            return self._fallback_from_db(
                project_id, db=db, before_id=before_id, limit=limit, actor_id=actor_id, entity_type=entity_type
            )

        items: list[ChangeLogEntry] = []
        next_cursor = None

        actor_str = str(actor_id) if actor_id else None
        entity_type_clean = entity_type.strip().lower() if entity_type else None

        for entry_id, fields in raw_entries:
            if before_id and entry_id == before_id:
                continue

            if actor_str and fields.get("actor_user_id") != actor_str:
                continue

            if entity_type_clean and fields.get("entity_type", "").lower() != entity_type_clean:
                continue

            if len(items) < limit:
                try:
                    meta = json.loads(fields.get("metadata", "{}"))
                except Exception:
                    meta = {}

                occurred = datetime.fromisoformat(fields["occurred_at"])
                actor_user_id = UUID(fields["actor_user_id"]) if fields.get("actor_user_id") else None
                diag_id = UUID(fields["diagram_id"]) if fields.get("diagram_id") else None

                items.append(
                    ChangeLogEntry(
                        id=entry_id,
                        project_id=project_id,
                        occurred_at=occurred,
                        actor_user_id=actor_user_id,
                        source=fields.get("source", "ui"),
                        module=fields.get("module", ""),
                        action=fields.get("action", ""),
                        entity_type=fields.get("entity_type") or None,
                        entity_id=fields.get("entity_id") or None,
                        diagram_id=diag_id,
                        summary=fields.get("summary", ""),
                        metadata=meta,
                    )
                )
            else:
                next_cursor = items[-1].id
                break

        if not next_cursor and len(raw_entries) == count and len(items) == limit:
            next_cursor = items[-1].id

        return ChangeLogPage(items=items, next_cursor=next_cursor, source="redis")

    def _fallback_from_db(
        self,
        project_id: UUID,
        *,
        db: Session | None,
        before_id: str | None,
        limit: int,
        actor_id: UUID | None,
        entity_type: str | None,
    ) -> ChangeLogPage:
        if db is None:
            return ChangeLogPage(items=[], next_cursor=None, source="postgres_fallback")

        query = select(AuditLog).where(AuditLog.project_id == project_id)
        if actor_id:
            query = query.where(AuditLog.user_id == actor_id)

        query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())

        if before_id:
            try:
                before_uuid = UUID(before_id)
                target = db.get(AuditLog, before_uuid)
                if target:
                    query = query.where(AuditLog.created_at < target.created_at)
            except Exception:
                pass

        results = list(db.scalars(query.limit(limit + 1)))
        has_more = len(results) > limit
        selected = results[:limit]

        items = []
        for log in selected:
            meta = log.metadata_json or {}
            ent_type = None
            ent_id = None
            for key in (
                "class_id",
                "relationship_id",
                "method_id",
                "attribute_id",
                "parameter_id",
                "diagram_id",
                "preset_id",
                "version_id",
                "member_id",
                "invitation_id",
            ):
                if key in meta:
                    ent_type = key.replace("_id", "")
                    ent_id = str(meta[key])
                    break

            diag_id = None
            if "diagram_id" in meta:
                try:
                    diag_id = UUID(str(meta["diagram_id"]))
                except Exception:
                    pass

            items.append(
                ChangeLogEntry(
                    id=str(log.id),
                    project_id=project_id,
                    occurred_at=log.created_at,
                    actor_user_id=log.user_id,
                    source="system" if log.user_id is None else "ui",
                    module=log.module,
                    action=log.action,
                    entity_type=ent_type,
                    entity_id=ent_id,
                    diagram_id=diag_id,
                    summary=build_summary(log.action, meta),
                    metadata=meta,
                )
            )

        next_cursor = str(selected[-1].id) if (has_more and selected) else None
        return ChangeLogPage(items=items, next_cursor=next_cursor, source="postgres_fallback")

    def resolve_names(self, db: Session, page: ChangeLogPage) -> ChangeLogPage:
        user_ids = {item.actor_user_id for item in page.items if item.actor_user_id}
        if not user_ids:
            return page

        users = db.scalars(select(User).where(User.id.in_(user_ids))).all()
        name_map = {
            u.id: (
                u.full_name
                if getattr(u, "full_name", None)
                else getattr(u, "email", "Usuario").split("@")[0]
            )
            for u in users
        }

        for item in page.items:
            if item.actor_user_id in name_map:
                item.actor_display_name = name_map[item.actor_user_id]
        return page
