"""Routers para gestión de invitaciones al proyecto (V2.3)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.proyectos_colaboracion.schemas.invitation import (
    InvitationCreateRequest,
    InvitationResponse,
)
from app.modules.proyectos_colaboracion.schemas.project import ProjectMemberResponse
from app.modules.proyectos_colaboracion.services.invitation_service import (
    InvitationService,
)

router = APIRouter(prefix="/projects", tags=["invitaciones"])
my_router = APIRouter(prefix="/invitations", tags=["invitaciones"])


# 1. Crear invitación (organizador)
@router.post(
    "/{project_id}/invitations",
    status_code=status.HTTP_201_CREATED,
    response_model=InvitationResponse,
)
def create_invitation(
    project_id: UUID,
    payload: InvitationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationResponse:
    service = InvitationService(db)
    invitation = service.invite(project_id, payload, current_user.id)
    return service.to_response(invitation)


# 2. Listar invitaciones por proyecto y estado (organizador)
@router.get(
    "/{project_id}/invitations",
    response_model=list[InvitationResponse],
)
def list_project_invitations(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status: str | None = Query(default=None),
) -> list[InvitationResponse]:
    service = InvitationService(db)
    items = service.list_for_project(project_id, current_user.id, status=status)
    return [service.to_response(item) for item in items]


# 3. Revocar invitación (organizador)
@router.delete(
    "/{project_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_invitation(
    project_id: UUID,
    invitation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = InvitationService(db)
    service.revoke(project_id, invitation_id, current_user.id)


# 4. Bandeja del invitado: mis invitaciones pendientes
@my_router.get("/me", response_model=list[InvitationResponse])
def list_my_invitations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[InvitationResponse]:
    service = InvitationService(db)
    items = service.list_mine(current_user)
    return [service.to_response(item) for item in items]


# 5. Bandeja del invitado: aceptar invitación
@my_router.post(
    "/{invitation_id}/accept",
    response_model=ProjectMemberResponse,
)
def accept_invitation(
    invitation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectMemberResponse:
    service = InvitationService(db)
    member = service.accept(invitation_id, current_user)
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        project_role=member.project_role,
        joined_at=member.joined_at,
        full_name=current_user.full_name,
        email=current_user.email,
    )


# 6. Bandeja del invitado: rechazar invitación
@my_router.post(
    "/{invitation_id}/reject",
    response_model=InvitationResponse,
)
def reject_invitation(
    invitation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationResponse:
    service = InvitationService(db)
    invitation = service.reject(invitation_id, current_user)
    return service.to_response(invitation)
