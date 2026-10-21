"""Repositorio de base de datos para invitaciones a proyectos (V2.3)."""

from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.proyectos_colaboracion.models.project_invitation import ProjectInvitation


class InvitationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, invitation: ProjectInvitation) -> ProjectInvitation:
        self.db.add(invitation)
        self.db.flush()
        return invitation

    def get(self, invitation_id: UUID) -> ProjectInvitation | None:
        return self.db.get(ProjectInvitation, invitation_id)

    def pending_for(self, project_id: UUID, email: str) -> ProjectInvitation | None:
        statement = select(ProjectInvitation).where(
            ProjectInvitation.project_id == project_id,
            func.lower(ProjectInvitation.invited_email) == email.strip().lower(),
            ProjectInvitation.status == "pending",
        )
        return self.db.scalar(statement)

    def list_by_project(
        self, project_id: UUID, status: str | None = None
    ) -> list[ProjectInvitation]:
        statement = select(ProjectInvitation).where(ProjectInvitation.project_id == project_id)
        if status:
            statement = statement.where(ProjectInvitation.status == status)
        statement = statement.order_by(ProjectInvitation.created_at.desc())
        return list(self.db.scalars(statement).all())

    def list_pending_for_email(self, email: str) -> list[ProjectInvitation]:
        statement = (
            select(ProjectInvitation)
            .where(
                func.lower(ProjectInvitation.invited_email) == email.strip().lower(),
                ProjectInvitation.status == "pending",
            )
            .order_by(ProjectInvitation.created_at.desc())
        )
        return list(self.db.scalars(statement).all())
