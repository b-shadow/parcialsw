from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, audit_log: AuditLog) -> AuditLog:
        self.db.add(audit_log)
        self.db.flush()
        return audit_log

    def list(
        self,
        *,
        module: str | None = None,
        action: str | None = None,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        query = select(AuditLog)
        if module:
            query = query.where(AuditLog.module == module)
        if action:
            query = query.where(AuditLog.action == action)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if project_id:
            query = query.where(AuditLog.project_id == project_id)
        query = query.order_by(AuditLog.created_at.desc()).limit(limit)
        return list(self.db.scalars(query))
