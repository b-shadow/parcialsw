from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.proyectos_colaboracion.models import (
    CollaborationEvent,
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

    def remove_member(self, project_id: UUID, member_id: UUID, user_id: UUID) -> UUID:
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
        removed_user_id = member.user_id
        self.members.delete(member)
        self.audit.record(
            module="proyectos_colaboracion",
            action="REMOVE_PROJECT_MEMBER",
            user_id=user_id,
            project_id=project_id,
            metadata={"member_id": str(member_id)},
        )
        self.db.commit()
        return removed_user_id

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
        ensure_project_exists(self.projects.get_for_update(project_id))
        ensure_organizer(self.members.get_membership(project_id, user_id))
        version = self._create_version_record(
            project_id=project_id,
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            snapshot=self._build_project_snapshot(project_id, user_id),
        )
        self.audit.record(
            module="proyectos_colaboracion",
            action="CREATE_PROJECT_VERSION",
            user_id=user_id,
            project_id=project_id,
            metadata={"version_number": version.version_number},
        )
        self.db.commit()
        self.db.refresh(version)
        return version

    def list_versions(self, project_id: UUID, user_id: UUID) -> list[dict]:
        ensure_project_exists(self.projects.get(project_id))
        ensure_organizer(self.members.get_membership(project_id, user_id))
        return [
            {
                **self._version_dict(version),
                "created_by_name": user_name,
            }
            for version, user_name in self.projects.list_versions(project_id)
        ]

    def list_changes(self, project_id: UUID, user_id: UUID, limit: int) -> list[dict]:
        ensure_project_exists(self.projects.get(project_id))
        self._require_member(project_id, user_id)
        return [
            {
                "id": event.id,
                "project_id": event.project_id,
                "diagram_id": event.diagram_id,
                "user_id": event.user_id,
                "user_name": user_name,
                "client_event_id": event.client_event_id,
                "sequence_number": event.sequence_number,
                "event_type": event.event_type,
                "element_type": event.element_type,
                "element_id": event.element_id,
                "base_version": event.base_version,
                "payload": event.payload,
                "created_at": event.created_at,
            }
            for event, user_name in self.projects.list_changes(project_id, limit)
        ]

    def restore_version(
        self, project_id: UUID, version_id: UUID, user_id: UUID
    ) -> dict:
        project = ensure_project_exists(self.projects.get_for_update(project_id))
        ensure_organizer(self.members.get_membership(project_id, user_id))
        version = self.projects.get_version(version_id)
        if version is None or version.project_id != project.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version del proyecto no encontrada",
            )
        if version.snapshot.get("schema_version") != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta version antigua no contiene un snapshot restaurable",
            )

        backup = self._create_version_record(
            project_id=project_id,
            user_id=user_id,
            name=f"Respaldo antes de restaurar v{version.version_number}",
            description="Snapshot automatico de seguridad previo a la restauracion.",
            snapshot=self._build_project_snapshot(project_id, user_id),
        )
        from app.modules.modelado_uml.services.uml_service import UmlService

        restored_ids = UmlService(self.db).restore_project_snapshot(
            project_id, version.snapshot, user_id
        )
        version.status = "restored"
        restore_event = CollaborationEvent(
            project_id=project_id,
            diagram_id=None,
            user_id=user_id,
            client_event_id=uuid4(),
            sequence_number=self.projects.next_event_sequence(project_id),
            event_type="RESTORE_VERSION",
            element_type=None,
            element_id=None,
            base_version=None,
            payload={
                "restored_version": version.version_number,
                "backup_version": backup.version_number,
            },
        )
        self.db.add(restore_event)
        self.audit.record(
            module="proyectos_colaboracion",
            action="RESTORE_PROJECT_VERSION",
            user_id=user_id,
            project_id=project_id,
            metadata={
                "restored_version": version.version_number,
                "backup_version": backup.version_number,
            },
        )
        self.db.commit()
        self.db.refresh(version)
        self.db.refresh(backup)
        return {
            "restored_version": self._version_dict(version),
            "backup_version": self._version_dict(backup),
            "restored_diagram_ids": restored_ids,
            "event_sequence": restore_event.sequence_number,
            "event_id": restore_event.id,
            "client_event_id": restore_event.client_event_id,
        }

    def record_collaboration_event(
        self,
        *,
        project_id: UUID,
        diagram_id: UUID | None,
        user_id: UUID,
        client_event_id: UUID,
        event_type: str,
        element_type: str | None,
        element_id: UUID | None,
        base_version: int | None,
        payload: dict,
    ) -> tuple[CollaborationEvent, bool]:
        self._require_member(project_id, user_id)
        if diagram_id is not None:
            from app.modules.modelado_uml.models import UmlDiagram

            diagram = self.db.get(UmlDiagram, diagram_id)
            if diagram is None or diagram.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El diagrama no pertenece al proyecto colaborativo",
                )
        ensure_project_exists(self.projects.get_for_update(project_id))
        existing = self.projects.get_event_by_client_id(
            project_id, user_id, client_event_id
        )
        if existing is not None:
            return existing, False
        event = CollaborationEvent(
            project_id=project_id,
            diagram_id=diagram_id,
            user_id=user_id,
            client_event_id=client_event_id,
            sequence_number=self.projects.next_event_sequence(project_id),
            event_type=event_type,
            element_type=element_type,
            element_id=element_id,
            base_version=base_version,
            payload=payload,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event, True

    def _create_version_record(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None,
        snapshot: dict,
    ) -> ProjectVersion:
        version = ProjectVersion(
            project_id=project_id,
            created_by_user_id=user_id,
            version_number=self.projects.next_version_number(project_id),
            name=name,
            description=description,
            snapshot=snapshot,
            status="saved",
        )
        self.db.add(version)
        self.db.flush()
        return version

    def _build_project_snapshot(self, project_id: UUID, user_id: UUID) -> dict:
        from app.modules.modelado_uml.services.uml_service import UmlService

        uml_service = UmlService(self.db)
        diagrams = uml_service.uml.list_diagrams_by_project(project_id)
        return {
            "schema_version": 1,
            "project_id": str(project_id),
            "diagrams": [
                uml_service._build_internal_model(diagram).model_dump(mode="json")
                for diagram in diagrams
            ],
        }

    @staticmethod
    def _version_dict(version: ProjectVersion) -> dict:
        return {
            "id": version.id,
            "project_id": version.project_id,
            "created_by_user_id": version.created_by_user_id,
            "version_number": version.version_number,
            "name": version.name,
            "description": version.description,
            "snapshot": version.snapshot,
            "status": version.status,
            "created_at": version.created_at,
            "created_by_name": None,
        }

    def _require_member(self, project_id: UUID, user_id: UUID) -> ProjectMember:
        from app.modules.proyectos_colaboracion.validators.project_validator import (
            ensure_membership,
        )

        return ensure_membership(self.members.get_membership(project_id, user_id))
