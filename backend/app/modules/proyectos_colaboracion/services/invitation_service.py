"""Servicio para gestión de invitaciones al proyecto (V2.3)."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import User
from app.modules.notificaciones.schemas.notification import NotificationDeepLink
from app.modules.notificaciones.services.notification_service import (
    DomainNotificationEvent,
    NotificationService,
)
from app.modules.proyectos_colaboracion.models.project_invitation import ProjectInvitation
from app.modules.proyectos_colaboracion.models.project_member import ProjectMember
from app.modules.proyectos_colaboracion.repositories.invitation_repository import (
    InvitationRepository,
)
from app.modules.proyectos_colaboracion.repositories.member_repository import (
    MemberRepository,
)
from app.modules.proyectos_colaboracion.repositories.project_repository import (
    ProjectRepository,
)
from app.modules.proyectos_colaboracion.schemas.invitation import (
    InvitationCreateRequest,
    InvitationResponse,
)
from app.modules.proyectos_colaboracion.services.project_service import ProjectService
from app.modules.proyectos_colaboracion.validators.project_validator import (
    ensure_project_exists,
    ensure_project_permission,
)


class InvitationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.invitations = InvitationRepository(db)
        self.projects = ProjectRepository(db)
        self.members = MemberRepository(db)
        self.project_service = ProjectService(db)

    def _check_expiration(self, invitation: ProjectInvitation) -> ProjectInvitation:
        if (
            invitation.status == "pending"
            and invitation.expires_at is not None
            and invitation.expires_at <= datetime.now(UTC)
        ):
            invitation.status = "expired"
            self.db.commit()
            self.db.refresh(invitation)
        return invitation

    def to_response(self, invitation: ProjectInvitation) -> InvitationResponse:
        self._check_expiration(invitation)
        project = self.projects.get(invitation.project_id)
        inviter = self.db.get(User, invitation.invited_by_user_id)
        inviter_name = (
            inviter.full_name or inviter.email.split("@")[0]
            if inviter
            else "Organizador"
        )
        project_name = project.name if project else "Proyecto"
        return InvitationResponse(
            id=invitation.id,
            project_id=invitation.project_id,
            project_name=project_name,
            invited_email=invitation.invited_email,
            project_role=invitation.project_role,
            status=invitation.status,
            invited_by_name=inviter_name,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )

    def invite(
        self, project_id: UUID, payload: InvitationCreateRequest, user_id: UUID
    ) -> ProjectInvitation:
        ensure_project_exists(self.projects.get(project_id))
        ensure_project_permission(self.db, project_id, user_id, "members.manage")

        clean_email = payload.email.strip().lower()

        # Comprobar si ya existe un usuario con este correo y ya es miembro
        user = self.db.scalar(select(User).where(func.lower(User.email) == clean_email))
        if user is not None and self.members.get_membership(project_id, user.id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="MEMBER_ALREADY_EXISTS",
            )

        # Comprobar si ya hay una invitación pendiente para este correo en este proyecto
        pending = self.invitations.pending_for(project_id, clean_email)
        if pending is not None:
            self._check_expiration(pending)
            if pending.status == "pending":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="INVITATION_ALREADY_PENDING",
                )

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=7)
        invitation = ProjectInvitation(
            id=uuid4(),
            project_id=project_id,
            invited_by_user_id=user_id,
            invited_user_id=user.id if user else None,
            invited_email=clean_email,
            project_role=payload.project_role,
            status="pending",
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        self.invitations.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)

        # Notificar al usuario invitado si ya está registrado en el sistema
        if user is not None:
            NotificationService(self.db).record(
                DomainNotificationEvent(
                    type="PROJECT_INVITATION_RECEIVED",
                    category="access",
                    title="Invitación a proyecto",
                    body=f"Te han invitado a unirte a un proyecto con rol {invitation.project_role}.",
                    recipient_user_ids={user.id},
                    dedup_entity_id=invitation.id,
                    project_id=project_id,
                    actor_user_id=user_id,
                    deep_link=NotificationDeepLink(route_name="projects"),
                )
            )
            self.db.commit()

        return invitation

    def list_for_project(
        self, project_id: UUID, user_id: UUID, status: str | None = None
    ) -> list[ProjectInvitation]:
        ensure_project_exists(self.projects.get(project_id))
        ensure_project_permission(self.db, project_id, user_id, "members.manage")
        items = self.invitations.list_by_project(project_id, status)
        for item in items:
            self._check_expiration(item)
        if status:
            items = [item for item in items if item.status == status]
        return items

    def revoke(self, project_id: UUID, invitation_id: UUID, user_id: UUID) -> None:
        ensure_project_exists(self.projects.get(project_id))
        ensure_project_permission(self.db, project_id, user_id, "members.manage")
        invitation = self.invitations.get(invitation_id)
        if invitation is None or invitation.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVITATION_NOT_FOUND",
            )
        self._check_expiration(invitation)
        if invitation.status == "pending":
            invitation.status = "revoked"
            invitation.responded_at = datetime.now(UTC)
            self.db.commit()

    def list_mine(self, user: User) -> list[ProjectInvitation]:
        items = self.invitations.list_pending_for_email(user.email)
        active: list[ProjectInvitation] = []
        for item in items:
            self._check_expiration(item)
            if item.status == "pending":
                active.append(item)
        return active

    def accept(self, invitation_id: UUID, user: User) -> ProjectMember:
        invitation = self.invitations.get(invitation_id)
        if invitation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVITATION_NOT_FOUND",
            )
        if invitation.invited_email.strip().lower() != user.email.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVITATION_NOT_FOUND",
            )
        self._check_expiration(invitation)
        if invitation.status == "expired":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="INVITATION_EXPIRED",
            )
        if invitation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INVITATION_STATUS",
            )

        invitation.status = "accepted"
        invitation.responded_at = datetime.now(UTC)
        invitation.invited_user_id = user.id
        self.db.commit()

        member = self.project_service.add_member_from_invitation(invitation, user.id)

        NotificationService(self.db).record(
            DomainNotificationEvent(
                type="PROJECT_INVITATION_ACCEPTED",
                category="access",
                title="Invitación aceptada",
                body=f"{user.full_name or user.email} aceptó la invitación al proyecto.",
                recipient_user_ids={invitation.invited_by_user_id},
                dedup_entity_id=f"{invitation.id}:accepted",
                project_id=invitation.project_id,
                actor_user_id=user.id,
                deep_link=NotificationDeepLink(
                    route_name="project_management",
                    params={"project_id": str(invitation.project_id)},
                ),
            )
        )
        self.db.commit()
        return member

    def reject(self, invitation_id: UUID, user: User) -> ProjectInvitation:
        invitation = self.invitations.get(invitation_id)
        if invitation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVITATION_NOT_FOUND",
            )
        if invitation.invited_email.strip().lower() != user.email.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVITATION_NOT_FOUND",
            )
        self._check_expiration(invitation)
        if invitation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_INVITATION_STATUS",
            )

        invitation.status = "rejected"
        invitation.responded_at = datetime.now(UTC)
        invitation.invited_user_id = user.id
        self.db.commit()
        self.db.refresh(invitation)

        NotificationService(self.db).record(
            DomainNotificationEvent(
                type="PROJECT_INVITATION_REJECTED",
                category="access",
                title="Invitación rechazada",
                body=f"{user.full_name or user.email} rechazó la invitación al proyecto.",
                recipient_user_ids={invitation.invited_by_user_id},
                dedup_entity_id=f"{invitation.id}:rejected",
                project_id=invitation.project_id,
                actor_user_id=user.id,
                deep_link=NotificationDeepLink(
                    route_name="project_management",
                    params={"project_id": str(invitation.project_id)},
                ),
            )
        )
        self.db.commit()
        return invitation
