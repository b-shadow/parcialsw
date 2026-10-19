from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import User
from app.modules.proyectos_colaboracion.models import (
    CollaborationEvent,
    Project,
    ProjectMember,
    ProjectVersion,
)


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

    def get_for_update(self, project_id: UUID) -> Project | None:
        return self.db.scalar(
            select(Project).where(Project.id == project_id).with_for_update()
        )

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

    def get_version(self, version_id: UUID) -> ProjectVersion | None:
        return self.db.get(ProjectVersion, version_id)

    def list_versions(self, project_id: UUID) -> list[tuple[ProjectVersion, str]]:
        statement = (
            select(ProjectVersion, User.full_name)
            .join(User, User.id == ProjectVersion.created_by_user_id)
            .where(ProjectVersion.project_id == project_id)
            .order_by(ProjectVersion.version_number.desc())
        )
        return list(self.db.execute(statement).tuples())

    def list_changes(
        self, project_id: UUID, limit: int = 100
    ) -> list[tuple[CollaborationEvent, str]]:
        statement = (
            select(CollaborationEvent, User.full_name)
            .join(User, User.id == CollaborationEvent.user_id)
            .where(CollaborationEvent.project_id == project_id)
            .order_by(CollaborationEvent.sequence_number.desc())
            .limit(max(1, min(limit, 250)))
        )
        return list(self.db.execute(statement).tuples())

    def list_changes_after(
        self, project_id: UUID, after_sequence: int, limit: int = 250
    ) -> list[tuple[CollaborationEvent, str]]:
        statement = (
            select(CollaborationEvent, User.full_name)
            .join(User, User.id == CollaborationEvent.user_id)
            .where(
                CollaborationEvent.project_id == project_id,
                CollaborationEvent.sequence_number > after_sequence,
            )
            .order_by(CollaborationEvent.sequence_number)
            .limit(max(1, min(limit, 250)))
        )
        return list(self.db.execute(statement).tuples())

    def list_activity_before(
        self, project_id: UUID, before_sequence: int | None, limit: int,
        event_types: set[str] | None = None,
    ) -> list[tuple[CollaborationEvent, str]]:
        statement = (
            select(CollaborationEvent, User.full_name)
            .join(User, User.id == CollaborationEvent.user_id)
            .where(CollaborationEvent.project_id == project_id)
        )
        if before_sequence is not None:
            statement = statement.where(CollaborationEvent.sequence_number < before_sequence)
        if event_types:
            statement = statement.where(CollaborationEvent.event_type.in_(event_types))
        return list(self.db.execute(
            statement.order_by(CollaborationEvent.sequence_number.desc())
            .limit(max(1, min(limit, 100)) + 1)
        ).tuples())

    def current_event_sequence(self, project_id: UUID) -> int:
        current = self.db.scalar(
            select(func.max(CollaborationEvent.sequence_number)).where(
                CollaborationEvent.project_id == project_id
            )
        )
        return current or 0

    def get_event_by_client_id(
        self, project_id: UUID, user_id: UUID, client_event_id: UUID
    ) -> CollaborationEvent | None:
        return self.db.scalar(
            select(CollaborationEvent).where(
                CollaborationEvent.project_id == project_id,
                CollaborationEvent.user_id == user_id,
                CollaborationEvent.client_event_id == client_event_id,
            )
        )

    def next_event_sequence(self, project_id: UUID) -> int:
        return self.current_event_sequence(project_id) + 1

