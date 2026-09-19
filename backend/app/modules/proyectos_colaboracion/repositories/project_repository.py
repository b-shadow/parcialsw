from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.proyectos_colaboracion.models import Project, ProjectMember, ProjectVersion


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        self.db.refresh(project)
        return project

    def get(self, project_id: UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def list_for_user(self, user_id: UUID) -> list[Project]:
        statement = (
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(self.db.scalars(statement))

    def next_version_number(self, project_id: UUID) -> int:
        versions = self.db.scalars(
            select(ProjectVersion.version_number)
            .where(ProjectVersion.project_id == project_id)
            .order_by(ProjectVersion.version_number.desc())
            .limit(1)
        ).first()
        return (versions or 0) + 1

