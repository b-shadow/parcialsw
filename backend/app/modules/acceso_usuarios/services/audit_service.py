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
        return self.repository.add(
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
