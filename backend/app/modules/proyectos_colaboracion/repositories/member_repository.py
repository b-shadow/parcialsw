from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.proyectos_colaboracion.models import ProjectMember


class MemberRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, member: ProjectMember) -> ProjectMember:
        self.db.add(member)
        self.db.flush()
        self.db.refresh(member)
        return member

    def get(self, member_id: UUID) -> ProjectMember | None:
        return self.db.get(ProjectMember, member_id)

    def get_membership(self, project_id: UUID, user_id: UUID) -> ProjectMember | None:
        return self.db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )

    def list_by_project(self, project_id: UUID) -> list[ProjectMember]:
        return list(
            self.db.scalars(
                select(ProjectMember)
                .where(ProjectMember.project_id == project_id)
                .order_by(ProjectMember.created_at)
            )
        )
