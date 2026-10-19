from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.proyectos_colaboracion.models import Project


class ProjectMutationGuard:
    """Shared PostgreSQL row lock for every versionable project mutation."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def acquire(self, project_id: UUID, expected_revision: int | None = None) -> Project:
        project = self.db.scalar(
            select(Project).where(Project.id == project_id).with_for_update()
        )
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROJECT_NOT_FOUND", "message": "Proyecto no encontrado"},
            )
        if expected_revision is not None and project.revision != expected_revision:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PROJECT_REVISION_CONFLICT",
                    "message": "El proyecto fue modificado por otra operacion",
                    "current_revision": project.revision,
                },
            )
        return project

    @staticmethod
    def advance(project: Project) -> int:
        project.revision += 1
        return project.revision
