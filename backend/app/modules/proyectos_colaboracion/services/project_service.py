from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.proyectos_colaboracion.models import (
    Project,
    ProjectMember,
    ProjectPermission,
    ProjectVersion,
)
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.repositories.project_repository import ProjectRepository
from app.modules.proyectos_colaboracion.schemas.project import (
    AddMemberRequest,
    PermissionRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    UpdateMemberRequest,
    VersionCreateRequest,
)
from app.modules.proyectos_colaboracion.validators.project_validator import (
    ensure_organizer,
    ensure_project_exists,
)

DEFAULT_ORGANIZER_PERMISSIONS = [
    "EDIT_UML",
    "GENERATE_CODE",
    "MANAGE_MEMBERS",
    "EXPORT_MODELS",
    "VIEW_REPORTS",
    "MANAGE_VERSIONS",
]


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.members = MemberRepository(db)
        self.audit = AuditService(db)

    def create_project(self, payload: ProjectCreateRequest, owner_id: UUID) -> Project:
        project = self.projects.add(
            Project(
                owner_id=owner_id,
                name=payload.name.strip(),
                description=payload.description,
                settings=payload.settings,
            )
        )
        member = self.members.add(
            ProjectMember(
                project_id=project.id,
                user_id=owner_id,
                project_role="ORGANIZADOR",
                joined_at=datetime.now(UTC),
            )
        )
        for permission in DEFAULT_ORGANIZER_PERMISSIONS:
            self.db.add(
                ProjectPermission(
                    member_id=member.id,
                    permission_code=permission,
                    is_allowed=True,
                )
            )
        self.audit.record(
            module="proyectos_colaboracion",
            action="CREATE_PROJECT",
            user_id=owner_id,
            project_id=project.id,
        )
        self.db.commit()
        self.db.refresh(project)
        return project

    def list_projects(self, user_id: UUID) -> list[Project]:
        return self.projects.list_for_user(user_id)

    def get_project(self, project_id: UUID, user_id: UUID) -> Project:
        project = ensure_project_exists(self.projects.get(project_id))
        ensure_project_exists(project)
        self._require_member(project_id, user_id)
        return project

    def update_project(self, project_id: UUID, payload: ProjectUpdateRequest, user_id: UUID) -> Project:
        project = ensure_project_exists(self.projects.get(project_id))
        ensure_organizer(self.members.get_membership(project_id, user_id))
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        self.audit.record(
            module="proyectos_colaboracion",
            action="UPDATE_PROJECT",
            user_id=user_id,
            project_id=project_id,
        )
        self.db.commit()
        self.db.refresh(project)
        return project

    def archive_project(self, project_id: UUID, user_id: UUID) -> Project:
        return self.update_project(
            project_id,
            ProjectUpdateRequest(status="archived"),
            user_id,
        )

    def add_member(self, project_id: UUID, payload: AddMemberRequest, user_id: UUID) -> ProjectMember:
        ensure_project_exists(self.projects.get(project_id))
        ensure_organizer(self.members.get_membership(project_id, user_id))
        existing = self.members.get_membership(project_id, payload.user_id)
        if existing is not None:
            return existing
        member = self.members.add(
            ProjectMember(
                project_id=project_id,
                user_id=payload.user_id,
                project_role=payload.project_role,
                joined_at=datetime.now(UTC),
            )
        )
        self.audit.record(
            module="proyectos_colaboracion",
            action="ADD_PROJECT_MEMBER",
            user_id=user_id,
            project_id=project_id,
            metadata={"member_user_id": str(payload.user_id)},
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def list_members(self, project_id: UUID, user_id: UUID) -> list[ProjectMember]:
        self._require_member(project_id, user_id)
        return self.members.list_by_project(project_id)

    def update_member(
        self, project_id: UUID, member_id: UUID, payload: UpdateMemberRequest, user_id: UUID
    ) -> ProjectMember:
        project = ensure_project_exists(self.projects.get(project_id))
        ensure_organizer(self.members.get_membership(project_id, user_id))
        member = self.members.get(member_id)
        if member is None or member.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro de proyecto no encontrado",
            )
        if member.user_id == project.owner_id and payload.project_role != "ORGANIZADOR":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El propietario debe conservar rol ORGANIZADOR",
            )
        if member.project_role == "ORGANIZADOR" and payload.project_role != "ORGANIZADOR":
            organizers = [item for item in self.members.list_by_project(project_id) if item.project_role == "ORGANIZADOR"]
            if len(organizers) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El proyecto debe conservar al menos un organizador",
                )
        member.project_role = payload.project_role
        self.audit.record(
            module="proyectos_colaboracion",
            action="UPDATE_PROJECT_MEMBER",
            user_id=user_id,
            project_id=project_id,
            metadata={"member_id": str(member_id), "project_role": payload.project_role},
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, project_id: UUID, member_id: UUID, user_id: UUID) -> None:
        project = ensure_project_exists(self.projects.get(project_id))
        ensure_organizer(self.members.get_membership(project_id, user_id))
        member = self.members.get(member_id)
        if member is None or member.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro de proyecto no encontrado",
            )
        if member.user_id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede quitar al propietario del proyecto",
            )
        if member.project_role == "ORGANIZADOR":
            organizers = [item for item in self.members.list_by_project(project_id) if item.project_role == "ORGANIZADOR"]
            if len(organizers) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El proyecto debe conservar al menos un organizador",
                )
        self.members.delete(member)
        self.audit.record(
            module="proyectos_colaboracion",
            action="REMOVE_PROJECT_MEMBER",
            user_id=user_id,
            project_id=project_id,
            metadata={"member_id": str(member_id)},
        )
        self.db.commit()

    def set_permission(
        self, project_id: UUID, member_id: UUID, payload: PermissionRequest, user_id: UUID
    ) -> ProjectPermission:
        ensure_organizer(self.members.get_membership(project_id, user_id))
        member = self.members.get(member_id)
        if member is None or member.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro de proyecto no encontrado",
            )
        permission = self.db.scalar(
            select(ProjectPermission).where(
                ProjectPermission.member_id == member_id,
                ProjectPermission.permission_code == payload.permission_code,
            )
        )
        if permission is None:
            permission = ProjectPermission(
                member_id=member_id,
                permission_code=payload.permission_code,
                is_allowed=payload.is_allowed,
            )
            self.db.add(permission)
        else:
            permission.is_allowed = payload.is_allowed
        self.audit.record(
            module="proyectos_colaboracion",
            action="SET_PROJECT_PERMISSION",
            user_id=user_id,
            project_id=project_id,
            metadata={"member_id": str(member_id), "permission": payload.permission_code},
        )
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def create_version(
        self, project_id: UUID, payload: VersionCreateRequest, user_id: UUID
    ) -> ProjectVersion:
        ensure_project_exists(self.projects.get(project_id))
        self._require_member(project_id, user_id)
        version = ProjectVersion(
            project_id=project_id,
            created_by_user_id=user_id,
            version_number=self.projects.next_version_number(project_id),
            name=payload.name,
            description=payload.description,
            snapshot=payload.snapshot,
            status="saved",
        )
        self.db.add(version)
        self.audit.record(
            module="proyectos_colaboracion",
            action="CREATE_PROJECT_VERSION",
            user_id=user_id,
            project_id=project_id,
        )
        self.db.commit()
        self.db.refresh(version)
        return version

    def _require_member(self, project_id: UUID, user_id: UUID) -> ProjectMember:
        from app.modules.proyectos_colaboracion.validators.project_validator import (
            ensure_membership,
        )

        return ensure_membership(self.members.get_membership(project_id, user_id))
