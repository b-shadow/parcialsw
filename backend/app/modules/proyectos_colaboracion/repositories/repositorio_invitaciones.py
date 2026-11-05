"""Repositorio de base de datos para invitaciones a proyectos (V2.3)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.proyectos_colaboracion.models.invitacion_proyecto import InvitacionProyecto


class RepositorioInvitaciones:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, invitation: InvitacionProyecto) -> InvitacionProyecto:
        self.db.add(invitation)
        self.db.flush()
        return invitation

    def get(self, invitation_id: UUID) -> InvitacionProyecto | None:
        return self.db.get(InvitacionProyecto, invitation_id)

    def pendientes_para(self, project_id: UUID, email: str) -> InvitacionProyecto | None:
        statement = select(InvitacionProyecto).where(
            InvitacionProyecto.project_id == project_id,
            func.lower(InvitacionProyecto.invited_email) == email.strip().lower(),
            InvitacionProyecto.status == "pending",
        )
        return self.db.scalar(statement)

    def listar_por_proyecto(
        self, project_id: UUID, status: str | None = None
    ) -> list[InvitacionProyecto]:
        statement = select(InvitacionProyecto).where(InvitacionProyecto.project_id == project_id)
        if status:
            statement = statement.where(InvitacionProyecto.status == status)
        statement = statement.order_by(InvitacionProyecto.created_at.desc())
        return list(self.db.scalars(statement).all())

    def listar_pendientes_por_correo(self, email: str) -> list[InvitacionProyecto]:
        statement = (
            select(InvitacionProyecto)
            .where(
                func.lower(InvitacionProyecto.invited_email) == email.strip().lower(),
                InvitacionProyecto.status == "pending",
            )
            .order_by(InvitacionProyecto.created_at.desc())
        )
        return list(self.db.scalars(statement).all())
