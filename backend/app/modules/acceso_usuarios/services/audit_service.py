from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import AuditLog
from app.modules.acceso_usuarios.repositories.audit_repository import AuditRepository

SENSITIVE_AUDIT_KEYS = (
    "password", "token", "authorization", "secret", "private_key",
    "p256dh", "cookie", "database_url", "connection_string",
)


def sanitize_audit_metadata(value: object, *, depth: int = 0) -> object:
    if depth >= 5:
        return "[truncated]"
    if isinstance(value, dict):
        return {
            str(key)[:80]: sanitize_audit_metadata(child, depth=depth + 1)
            for key, child in list(value.items())[:50]
            if not any(part in str(key).casefold() for part in SENSITIVE_AUDIT_KEYS)
        }
    if isinstance(value, list):
        return [sanitize_audit_metadata(child, depth=depth + 1) for child in value[:50]]
    if isinstance(value, str):
        return value[:500]
    return value


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AuditRepository(db)

    def record(
        self,
        *,
        module: str,
        action: str,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        result: str = "success",
        detail: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        log = self.repository.add(
            AuditLog(
                user_id=user_id,
                project_id=project_id,
                module=module,
                action=action,
                result=result,
                detail=detail,
                metadata_json=sanitize_audit_metadata(metadata or {}),
            )
        )

        if project_id is not None:
            from app.core.changelog.contracts import PendingChange
            from app.core.changelog.hooks import queue_change

            source = (
                "ai"
                if self.db.info.get("change_origin") == "ai"
                else ("system" if user_id is None else "ui")
            )
            meta = metadata or {}
            entity_type = None
            entity_id = None
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
                    entity_type = key.replace("_id", "")
                    entity_id = str(meta[key])
                    break

            diagram_id_val = None
            if "diagram_id" in meta:
                try:
                    diagram_id_val = UUID(str(meta["diagram_id"]))
                except Exception:
                    pass

            queue_change(
                self.db,
                PendingChange(
                    project_id=project_id,
                    actor_user_id=user_id,
                    source=source,
                    module=module,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    diagram_id=diagram_id_val,
                    metadata=meta,
                ),
            )

        return log

    def list_logs(
        self,
        *,
        module: str | None = None,
        action: str | None = None,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        return self.repository.list(
            module=module,
            action=action,
            user_id=user_id,
            project_id=project_id,
            limit=max(1, min(limit, 500)),
        )
