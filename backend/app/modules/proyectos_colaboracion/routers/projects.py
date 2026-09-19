from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.proyectos_colaboracion.models import Project, ProjectMember, ProjectPermission
from app.modules.proyectos_colaboracion.schemas.project import (
    AddMemberRequest,
    PermissionRequest,
    ProjectCreateRequest,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdateRequest,
    VersionCreateRequest,
    VersionResponse,
)
from app.modules.proyectos_colaboracion.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["proyectos"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Project:
    return ProjectService(db).create_project(payload, current_user.id)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Project]:
    return ProjectService(db).list_projects(current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Project:
    return ProjectService(db).get_project(project_id, current_user.id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Project:
    return ProjectService(db).update_project(project_id, payload, current_user.id)


@router.delete("/{project_id}", response_model=ProjectResponse)
def archive_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Project:
    return ProjectService(db).archive_project(project_id, current_user.id)


@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
def add_member(
    project_id: UUID,
    payload: AddMemberRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectMember:
    return ProjectService(db).add_member(project_id, payload, current_user.id)


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def list_members(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ProjectMember]:
    return ProjectService(db).list_members(project_id, current_user.id)


@router.post("/{project_id}/members/{member_id}/permissions")
def set_permission(
    project_id: UUID,
    member_id: UUID,
    payload: PermissionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    permission: ProjectPermission = ProjectService(db).set_permission(
        project_id, member_id, payload, current_user.id
    )
    return {"id": str(permission.id), "permission_code": permission.permission_code}


@router.post("/{project_id}/versions", response_model=VersionResponse)
def create_version(
    project_id: UUID,
    payload: VersionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VersionResponse:
    return ProjectService(db).create_version(project_id, payload, current_user.id)

