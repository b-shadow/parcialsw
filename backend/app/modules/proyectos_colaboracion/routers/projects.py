from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.notificaciones.services import send_project_push, send_user_push
from app.modules.proyectos_colaboracion.models import Project, ProjectMember, ProjectPermission
from app.modules.proyectos_colaboracion.schemas.project import (
    AddMemberRequest,
    CollaborationEventResponse,
    PermissionRequest,
    ProjectCreateRequest,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdateRequest,
    UpdateMemberRequest,
    VersionCreateRequest,
    VersionResponse,
    VersionRestoreResponse,
)
from app.modules.proyectos_colaboracion.services.project_service import ProjectService
from app.websocket.connection_manager import manager

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
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectMember:
    member = ProjectService(db).add_member(project_id, payload, current_user.id)
    project = db.get(Project, project_id)
    background_tasks.add_task(
        send_user_push,
        member.user_id,
        {
            "title": "Nuevo proyecto compartido",
            "body": f"Te agregaron a {project.name if project else 'un proyecto'} como {member.project_role}.",
            "url": f"/proyectos/{project_id}",
            "tag": f"project-member-{project_id}",
        },
    )
    return member


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def list_members(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ProjectMember]:
    return ProjectService(db).list_members(project_id, current_user.id)


@router.patch("/{project_id}/members/{member_id}", response_model=ProjectMemberResponse)
def update_member(
    project_id: UUID,
    member_id: UUID,
    payload: UpdateMemberRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectMember:
    member = ProjectService(db).update_member(project_id, member_id, payload, current_user.id)
    background_tasks.add_task(
        send_user_push,
        member.user_id,
        {
            "title": "Rol de proyecto actualizado",
            "body": f"Tu rol ahora es {member.project_role}.",
            "url": f"/proyectos/{project_id}",
            "tag": f"project-role-{project_id}",
        },
    )
    return member


@router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: UUID,
    member_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    removed_user_id = ProjectService(db).remove_member(project_id, member_id, current_user.id)
    await manager.disconnect_user(str(project_id), str(removed_user_id))
    background_tasks.add_task(
        send_user_push,
        removed_user_id,
        {
            "title": "Acceso a proyecto retirado",
            "body": "Ya no formas parte de este proyecto.",
            "url": "/proyectos",
            "tag": f"project-removed-{project_id}",
        },
    )


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
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VersionResponse:
    version = ProjectService(db).create_version(project_id, payload, current_user.id)
    background_tasks.add_task(
        send_project_push,
        project_id,
        {
            "title": "Version de proyecto guardada",
            "body": f"{current_user.full_name} guardo la version {version.version_number}: {version.name}.",
            "url": f"/proyectos/{project_id}/colaborativo",
            "tag": f"project-version-{project_id}",
        },
        current_user.id,
    )
    return version


@router.get("/{project_id}/versions", response_model=list[VersionResponse])
def list_versions(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    return ProjectService(db).list_versions(project_id, current_user.id)


@router.post(
    "/{project_id}/versions/{version_id}/restore",
    response_model=VersionRestoreResponse,
)
async def restore_version(
    project_id: UUID,
    version_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    result = ProjectService(db).restore_version(project_id, version_id, current_user.id)
    await manager.broadcast(
        str(project_id),
        {
            "type": "UML_EVENT",
            "project_id": str(project_id),
            "diagram_id": None,
            "event_id": str(result["event_id"]),
            "client_event_id": str(result["client_event_id"]),
            "sequence_number": result["event_sequence"],
            "event_type": "RESTORE_VERSION",
            "user_id": str(current_user.id),
            "user_name": current_user.full_name,
            "payload": {
                "version_id": str(version_id),
                "restored_diagram_ids": [str(item) for item in result["restored_diagram_ids"]],
            },
        },
    )
    background_tasks.add_task(
        send_project_push,
        project_id,
        {
            "title": "Version de proyecto restaurada",
            "body": f"{current_user.full_name} restauro una version guardada.",
            "url": f"/proyectos/{project_id}/colaborativo",
            "tag": f"project-restore-{project_id}",
        },
        current_user.id,
    )
    return result


@router.get("/{project_id}/changes", response_model=list[CollaborationEventResponse])
def list_changes(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 100,
) -> list[dict]:
    return ProjectService(db).list_changes(project_id, current_user.id, limit)
