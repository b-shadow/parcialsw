"""Servicio para gestión de invitaciones al proyecto (V2.3)."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.models import Usuario
from app.modules.notificaciones.schemas.notificacion import EnlaceProfundoNotificacion
from app.modules.notificaciones.services.servicio_notificaciones import (
    EventoNotificacionDominio,
    ServicioNotificaciones,
)
from app.modules.proyectos_colaboracion.models.integrante_proyecto import IntegranteProyecto
from app.modules.proyectos_colaboracion.models.invitacion_proyecto import InvitacionProyecto
from app.modules.proyectos_colaboracion.repositories.repositorio_integrantes import (
    RepositorioIntegrantes,
)
from app.modules.proyectos_colaboracion.repositories.repositorio_invitaciones import (
    RepositorioInvitaciones,
)
from app.modules.proyectos_colaboracion.repositories.repositorio_proyectos import (
    RepositorioProyectos,
)
from app.modules.proyectos_colaboracion.schemas.invitacion import (
    RespuestaInvitacion,
    SolicitudCreacionInvitacion,
)
from app.modules.proyectos_colaboracion.services.servicio_proyectos import ServicioProyectos
from app.modules.proyectos_colaboracion.validators.validador_proyecto import (
    asegurar_permiso_proyecto,
    asegurar_proyecto_existente,
)


class ServicioInvitaciones:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.invitations = RepositorioInvitaciones(db)
        self.projects = RepositorioProyectos(db)
        self.members = RepositorioIntegrantes(db)
        self.project_service = ServicioProyectos(db)

    def _verificar_vencimiento(self, invitation: InvitacionProyecto) -> InvitacionProyecto:
        if (
            invitation.status == "pending"
            and invitation.expires_at is not None
            and invitation.expires_at <= datetime.now(UTC)
        ):
            invitation.status = "expired"
            self.db.commit()
            self.db.refresh(invitation)
        return invitation

    def convertir_a_respuesta(self, invitation: InvitacionProyecto) -> RespuestaInvitacion:
        self._verificar_vencimiento(invitation)
        project = self.projects.get(invitation.project_id)
        inviter = self.db.get(Usuario, invitation.invited_by_user_id)
        inviter_name = (
            inviter.full_name or inviter.email.split("@")[0]
            if inviter
            else "Organizador"
        )
        project_name = project.name if project else "Proyecto"
        return RespuestaInvitacion(
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

    def invitar(
        self, project_id: UUID, payload: SolicitudCreacionInvitacion, user_id: UUID
    ) -> InvitacionProyecto:
        asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_permiso_proyecto(self.db, project_id, user_id, "members.manage")

        clean_email = payload.email.strip().lower()

        # Comprobar si ya existe un usuario con este correo y ya es miembro
        user = self.db.scalar(select(Usuario).where(func.lower(Usuario.email) == clean_email))
        if user is not None and self.members.obtener_participacion(project_id, user.id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="MEMBER_ALREADY_EXISTS",
            )

        # Comprobar si ya hay una invitación pendiente para este correo en este proyecto
        pending = self.invitations.pendientes_para(project_id, clean_email)
        if pending is not None:
            self._verificar_vencimiento(pending)
            if pending.status == "pending":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="INVITATION_ALREADY_PENDING",
                )

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=7)
        invitation = InvitacionProyecto(
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
            ServicioNotificaciones(self.db).record(
                EventoNotificacionDominio(
                    type="PROJECT_INVITATION_RECEIVED",
                    category="access",
                    title="Invitación a proyecto",
                    body=f"Te han invitado a unirte a un proyecto con rol {invitation.project_role}.",
                    recipient_user_ids={user.id},
                    dedup_entity_id=invitation.id,
                    project_id=project_id,
                    actor_user_id=user_id,
                    deep_link=EnlaceProfundoNotificacion(route_name="projects"),
                )
            )
            self.db.commit()

        return invitation

    def listar_para_proyecto(
        self, project_id: UUID, user_id: UUID, status: str | None = None
    ) -> list[InvitacionProyecto]:
        asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_permiso_proyecto(self.db, project_id, user_id, "members.manage")
        items = self.invitations.listar_por_proyecto(project_id, status)
        for item in items:
            self._verificar_vencimiento(item)
        if status:
            items = [item for item in items if item.status == status]
        return items

    def revocar(self, project_id: UUID, invitation_id: UUID, user_id: UUID) -> None:
        asegurar_proyecto_existente(self.projects.get(project_id))
        asegurar_permiso_proyecto(self.db, project_id, user_id, "members.manage")
        invitation = self.invitations.get(invitation_id)
        if invitation is None or invitation.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="INVITATION_NOT_FOUND",
            )
        self._verificar_vencimiento(invitation)
        if invitation.status == "pending":
            invitation.status = "revoked"
            invitation.responded_at = datetime.now(UTC)
            self.db.commit()

    def listar_mias(self, user: Usuario) -> list[InvitacionProyecto]:
        items = self.invitations.listar_pendientes_por_correo(user.email)
        active: list[InvitacionProyecto] = []
        for item in items:
            self._verificar_vencimiento(item)
            if item.status == "pending":
                active.append(item)
        return active

    def aceptar(self, invitation_id: UUID, user: Usuario) -> IntegranteProyecto:
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
        self._verificar_vencimiento(invitation)
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

        member = self.project_service.agregar_integrante_desde_invitacion(invitation, user.id)

        ServicioNotificaciones(self.db).record(
            EventoNotificacionDominio(
                type="PROJECT_INVITATION_ACCEPTED",
                category="access",
                title="Invitación aceptada",
                body=f"{user.full_name or user.email} aceptó la invitación al proyecto.",
                recipient_user_ids={invitation.invited_by_user_id},
                dedup_entity_id=f"{invitation.id}:accepted",
                project_id=invitation.project_id,
                actor_user_id=user.id,
                deep_link=EnlaceProfundoNotificacion(
                    route_name="project_management",
                    params={"project_id": str(invitation.project_id)},
                ),
            )
        )
        self.db.commit()
        return member

    def reject(self, invitation_id: UUID, user: Usuario) -> InvitacionProyecto:
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
        self._verificar_vencimiento(invitation)
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

        ServicioNotificaciones(self.db).record(
            EventoNotificacionDominio(
                type="PROJECT_INVITATION_REJECTED",
                category="access",
                title="Invitación rechazada",
                body=f"{user.full_name or user.email} rechazó la invitación al proyecto.",
                recipient_user_ids={invitation.invited_by_user_id},
                dedup_entity_id=f"{invitation.id}:rejected",
                project_id=invitation.project_id,
                actor_user_id=user.id,
                deep_link=EnlaceProfundoNotificacion(
                    route_name="project_management",
                    params={"project_id": str(invitation.project_id)},
                ),
            )
        )
        self.db.commit()
        return invitation
