from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import AuditLog
from app.modules.acceso_usuarios.repositories.audit_repository import AuditRepository


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
                metadata_json=metadata or {},
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
