from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.proyectos_colaboracion.models import Project, ProjectMember, ProjectPermission
from app.modules.proyectos_colaboracion.schemas.project import (
    ActivityPageResponse,
    AddMemberRequest,
    CollaborationEventResponse,
    MyMembershipResponse,
    PermissionRequest,
    ProjectCreateRequest,
    ProjectMemberCandidateResponse,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdateRequest,
    RestorePreviewResponse,
    RestoreRequest,
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
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectMember:
    return ProjectService(db).add_member(project_id, payload, current_user.id)


@router.get(
    "/{project_id}/member-candidates",
    response_model=list[ProjectMemberCandidateResponse],
)
def list_member_candidates(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[User]:
    return ProjectService(db).list_member_candidates(project_id, current_user.id)


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def list_members(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ProjectMemberResponse]:
    members = ProjectService(db).list_members(project_id, current_user.id)
    users = {
        user.id: user
        for user in db.scalars(
            select(User).where(User.id.in_({member.user_id for member in members}))
        )
    }
    return [
        ProjectMemberResponse.model_validate(member).model_copy(
            update={
                "full_name": users[member.user_id].full_name,
                "email": users[member.user_id].email,
            }
        )
        for member in members
        if member.user_id in users
    ]


@router.get("/{project_id}/members/me", response_model=MyMembershipResponse)
def get_my_membership(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ProjectService(db).my_membership(project_id, current_user.id)


@router.patch("/{project_id}/members/{member_id}", response_model=ProjectMemberResponse)
def update_member(
    project_id: UUID,
    member_id: UUID,
    payload: UpdateMemberRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectMember:
    return ProjectService(db).update_member(project_id, member_id, payload, current_user.id)


@router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: UUID,
    member_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    removed_user_id = ProjectService(db).remove_member(project_id, member_id, current_user.id)
    await manager.disconnect_user(str(project_id), str(removed_user_id))


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
async def create_version(
    project_id: UUID,
    payload: VersionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> VersionResponse:
    version = ProjectService(db).create_version(
        project_id, payload, current_user.id, idempotency_key
    )
    await manager.broadcast(
        str(project_id),
        {
            "protocol_version": 2,
            "type": "PROJECT_VERSION_CREATED",
            "event_id": str(version.id),
            "project_id": str(project_id),
            "sequence_number": 0,
            "conversation_sequence": 0,
            "correlation_id": str(version.id),
            "occurred_at": version.created_at.isoformat(),
            "persistent": True,
            "actor": {"user_id": str(current_user.id), "display_name": current_user.full_name},
            "payload": {"version_id": str(version.id), "version_number": version.version_number},
        },
    )
    return version


@router.get("/{project_id}/versions", response_model=list[VersionResponse])
def list_versions(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    return ProjectService(db).list_versions(project_id, current_user.id)


@router.get(
    "/{project_id}/versions/{version_id}/restore-preview",
    response_model=RestorePreviewResponse,
)
async def restore_preview(
    project_id: UUID,
    version_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return await ProjectService(db).restore_preview(project_id, version_id, current_user.id)


@router.post(
    "/{project_id}/versions/{version_id}/restore",
    response_model=VersionRestoreResponse,
)
async def restore_version(
    project_id: UUID,
    version_id: UUID,
    payload: RestoreRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> dict:
    result = await ProjectService(db).restore_version(
        project_id,
        version_id,
        current_user.id,
        idempotency_key=idempotency_key,
        payload=payload,
    )
    if result["idempotent_replay"]:
        return result
    await manager.broadcast(
        str(project_id),
        {
            "protocol_version": 2,
            "type": "PROJECT_VERSION_RESTORED",
            "project_id": str(project_id),
            "diagram_id": None,
            "event_id": str(result["event_id"] or result["restore_operation_id"]),
            "sequence_number": result["event_sequence"] or 0,
            "conversation_sequence": 0,
            "correlation_id": str(result["restore_operation_id"]),
            "occurred_at": datetime.now(UTC).isoformat(),
            "persistent": True,
            "actor": {"user_id": str(current_user.id), "display_name": current_user.full_name},
            "payload": {
                "version_id": str(version_id),
                "restore_operation_id": str(result["restore_operation_id"]),
                "project_revision": result["project_revision"],
                "restored_diagram_ids": [str(item) for item in result["restored_diagram_ids"]],
            },
        },
    )
    await manager.broadcast(
        str(project_id),
        {
            "protocol_version": 2,
            "type": "PROJECT_STATE_INVALIDATED",
            "event_id": str(uuid4()),
            "project_id": str(project_id),
            "sequence_number": result["event_sequence"] or 0,
            "conversation_sequence": 0,
            "correlation_id": str(result["restore_operation_id"]),
            "occurred_at": datetime.now(UTC).isoformat(),
            "persistent": False,
            "actor": {"user_id": str(current_user.id), "display_name": current_user.full_name},
            "payload": {
                "project_revision": result["project_revision"],
                "reason": "version_restored",
            },
        },
    )
    return result


@router.get("/{project_id}/activity", response_model=ActivityPageResponse)
def list_activity(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    before_sequence: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    type: Annotated[list[str] | None, Query()] = None,
) -> dict:
    return ProjectService(db).list_activity(
        project_id,
        current_user.id,
        before_sequence=before_sequence,
        limit=limit,
        event_types=set(type or []),
    )


@router.get("/{project_id}/changes", response_model=list[CollaborationEventResponse])
def list_changes(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 100,
    after_sequence: int | None = None,
) -> list[dict]:
    return ProjectService(db).list_changes(project_id, current_user.id, limit, after_sequence)
