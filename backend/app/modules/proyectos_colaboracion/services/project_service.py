import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from pydantic import ValidationError
from pymongo.errors import PyMongoError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.nosql.errors import MongoUnavailableError
from app.modules.acceso_usuarios.models import User
from app.modules.acceso_usuarios.services.audit_service import AuditService
from app.modules.modelado_uml.models import UmlDiagram
from app.modules.modelado_uml.services.active_diagram_store import mark_uml_project_for_sync
from app.modules.notificaciones.schemas.notification import NotificationDeepLink
from app.modules.notificaciones.services.notification_service import (
    DomainNotificationEvent,
    NotificationService,
)
from app.modules.proyectos_colaboracion.models import (
    CollaborationEvent,
    Project,
    ProjectInvitation,
    ProjectMember,
    ProjectPermission,
    ProjectRestoreOperation,
    ProjectVersion,
)
from app.modules.proyectos_colaboracion.permissions import PERMISSION_CODES
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.repositories.project_repository import ProjectRepository
from app.modules.proyectos_colaboracion.schemas.project import (
    AddMemberRequest,
    PermissionRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    RestoreRequest,
    UpdateMemberRequest,
    VersionCreateRequest,
)
from app.modules.proyectos_colaboracion.schemas.snapshot import (
    ProjectSnapshotV2,
    SnapshotAiSettings,
    SnapshotFlutterTheme,
    SnapshotProject,
    canonicalize_project_snapshot,
    parse_project_snapshot,
    snapshot_sha256,
    upgrade_snapshot_v1_to_v2,
)
from app.modules.proyectos_colaboracion.services.project_mutation_guard import ProjectMutationGuard
from app.modules.proyectos_colaboracion.services.version_document_store import (
    UmlVersionDocumentStore,
    enqueue_version_document,
    persist_version_document,
)
from app.modules.proyectos_colaboracion.validators.project_validator import (
    ensure_project_exists,
    ensure_project_permission,
    member_permissions,
)

DEFAULT_ORGANIZER_PERMISSIONS = [
    "EDIT_UML",
    "GENERATE_CODE",
    "MANAGE_MEMBERS",
    "EXPORT_MODELS",
    "VIEW_REPORTS",
    "MANAGE_VERSIONS",
]

EVENT_ALIASES = {
    "CREATE_CLASS": "UML_CLASS_CREATED",
    "UPDATE_CLASS": "UML_CLASS_UPDATED",
    "DELETE_CLASS": "UML_CLASS_DELETED",
    "CREATE_ATTRIBUTE": "UML_ATTRIBUTE_CREATED",
    "UPDATE_ATTRIBUTE": "UML_ATTRIBUTE_UPDATED",
    "DELETE_ATTRIBUTE": "UML_ATTRIBUTE_DELETED",
    "CREATE_METHOD": "UML_METHOD_CREATED",
    "UPDATE_METHOD": "UML_METHOD_UPDATED",
    "DELETE_METHOD": "UML_METHOD_DELETED",
    "CREATE_RELATION": "UML_RELATIONSHIP_CREATED",
    "CREATE_RELATIONSHIP": "UML_RELATIONSHIP_CREATED",
    "UPDATE_RELATIONSHIP": "UML_RELATIONSHIP_UPDATED",
    "DELETE_RELATIONSHIP": "UML_RELATIONSHIP_DELETED",
    "MOVE_ELEMENT": "UML_ELEMENT_MOVED",
    "AI_UPDATE_DIAGRAM": "AI_ACTIONS_APPLIED",
    "RESTORE_VERSION": "PROJECT_VERSION_RESTORED",
}

logger = logging.getLogger(__name__)


def _optional_uuid(value: object) -> UUID | None:
    try:
        return UUID(str(value)) if value else None
    except (TypeError, ValueError):
        return None


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.members = MemberRepository(db)
        self.audit = AuditService(db)
        self.mutations = ProjectMutationGuard(db)
        self.version_documents = UmlVersionDocumentStore()

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
        self.db.add(
            UmlDiagram(
                project_id=project.id,
                created_by_user_id=owner_id,
                name=project.name,
                diagram_type="class",
                description=project.description,
                metadata_json={"project_diagram": True},
            )
        )
        mark_uml_project_for_sync(self.db, project.id)
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

    def my_membership(self, project_id: UUID, user_id: UUID) -> dict:
        member = self.members.get_membership(project_id, user_id)
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": "Sin acceso al proyecto"},
            )
        perms = member_permissions(self.db, member)
        return {
            "project_id": project_id,
            "user_id": user_id,
            "project_role": member.project_role,
            "permissions": sorted(perms),
        }

    def update_project(
        self, project_id: UUID, payload: ProjectUpdateRequest, user_id: UUID
    ) -> Project:
        project = self.mutations.acquire(project_id)
        ensure_project_permission(self.db, project_id, user_id, "project.update")
        values = payload.model_dump(exclude_unset=True)
        changed = any(
            field in {"name", "description", "settings"} and getattr(project, field) != value
            for field, value in values.items()
        )
        if changed:
            self.mutations.advance(project)
        for field, value in values.items():
            setattr(project, field, value)
        diagram = self.db.scalar(
            select(UmlDiagram)
            .where(UmlDiagram.project_id == project_id)
            .order_by(UmlDiagram.created_at)
            .limit(1)
        )
        if diagram is not None:
            if "name" in values:
                diagram.name = project.name
            if "description" in values:
                diagram.description = project.description
            if changed and ({"name", "description"} & values.keys()):
                mark_uml_project_for_sync(self.db, project.id)
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

    def add_member(
        self, project_id: UUID, payload: AddMemberRequest, user_id: UUID
    ) -> ProjectMember:
        ensure_project_exists(self.projects.get(project_id))
        ensure_project_permission(self.db, project_id, user_id, "members.manage")
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
        self._activity_event(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_MEMBER_ADDED",
            resource_type="project_member",
            resource_id=member.id,
            summary_key="activity.member_added",
            payload={"member_id": str(member.id), "project_role": member.project_role},
        )
        NotificationService(self.db).record(
            DomainNotificationEvent(
                type="PROJECT_MEMBER_ADDED",
                category="access",
                title="Nuevo proyecto compartido",
                body=f"Te agregaron al proyecto como {member.project_role}.",
                recipient_user_ids={member.user_id},
                dedup_entity_id=member.id,
                project_id=project_id,
                actor_user_id=user_id,
                resource_type="project_member",
                resource_id=member.id,
                deep_link=NotificationDeepLink(
                    route_name="project_management", params={"project_id": str(project_id)}
                ),
            )
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def add_member_from_invitation(self, invitation: ProjectInvitation, user_id: UUID) -> ProjectMember:
        ensure_project_exists(self.projects.get(invitation.project_id))
        existing = self.members.get_membership(invitation.project_id, user_id)
        if existing is not None:
            return existing
        member = self.members.add(
            ProjectMember(
                project_id=invitation.project_id,
                user_id=user_id,
                project_role=invitation.project_role,
                joined_at=datetime.now(UTC),
            )
        )
        self.audit.record(
            module="proyectos_colaboracion",
            action="ADD_PROJECT_MEMBER",
            user_id=invitation.invited_by_user_id,
            project_id=invitation.project_id,
            metadata={
                "member_user_id": str(user_id),
                "origin": "invitation",
                "invitation_id": str(invitation.id),
            },
        )
        self._activity_event(
            project_id=invitation.project_id,
            user_id=invitation.invited_by_user_id,
            event_type="PROJECT_MEMBER_ADDED",
            resource_type="project_member",
            resource_id=member.id,
            summary_key="activity.member_added",
            payload={
                "member_id": str(member.id),
                "project_role": member.project_role,
                "origin": "invitation",
            },
        )
        NotificationService(self.db).record(
            DomainNotificationEvent(
                type="PROJECT_MEMBER_ADDED",
                category="access",
                title="Nuevo proyecto compartido",
                body=f"Te agregaron al proyecto como {member.project_role}.",
                recipient_user_ids={member.user_id},
                dedup_entity_id=member.id,
                project_id=invitation.project_id,
                actor_user_id=invitation.invited_by_user_id,
                resource_type="project_member",
                resource_id=member.id,
                deep_link=NotificationDeepLink(
                    route_name="project_management",
                    params={"project_id": str(invitation.project_id)},
                ),
            )
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def list_members(self, project_id: UUID, user_id: UUID) -> list[ProjectMember]:
        self._require_member(project_id, user_id)
        return self.members.list_by_project(project_id)

    def list_member_candidates(self, project_id: UUID, user_id: UUID) -> list[User]:
        ensure_project_exists(self.projects.get(project_id))
        ensure_project_permission(self.db, project_id, user_id, "members.manage")
        member_user_ids = {
            member.user_id for member in self.members.list_by_project(project_id)
        }
        return list(
            self.db.scalars(
                select(User)
                .where(User.is_active.is_(True), User.id.not_in(member_user_ids))
                .order_by(User.full_name, User.email)
            )
        )

    def update_member(
        self, project_id: UUID, member_id: UUID, payload: UpdateMemberRequest, user_id: UUID
    ) -> ProjectMember:
        project = ensure_project_exists(self.projects.get(project_id))
        ensure_project_permission(self.db, project_id, user_id, "members.manage")
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
            organizers = [
                item
                for item in self.members.list_by_project(project_id)
                if item.project_role == "ORGANIZADOR"
            ]
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
        self._activity_event(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_MEMBER_ROLE_CHANGED",
            resource_type="project_member",
            resource_id=member.id,
            summary_key="activity.member_role_changed",
            payload={"member_id": str(member.id), "project_role": member.project_role},
        )
        NotificationService(self.db).record(
            DomainNotificationEvent(
                type="PROJECT_MEMBER_ROLE_CHANGED",
                category="access",
                title="Rol de proyecto actualizado",
                body=f"Tu rol ahora es {member.project_role}.",
                recipient_user_ids={member.user_id},
                dedup_entity_id=f"{member.id}:{member.project_role}",
                project_id=project_id,
                actor_user_id=user_id,
                resource_type="project_member",
                resource_id=member.id,
                deep_link=NotificationDeepLink(
                    route_name="project_management", params={"project_id": str(project_id)}
                ),
            )
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, project_id: UUID, member_id: UUID, user_id: UUID) -> UUID:
        project = ensure_project_exists(self.projects.get(project_id))
        ensure_project_permission(self.db, project_id, user_id, "members.manage")
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
            organizers = [
                item
                for item in self.members.list_by_project(project_id)
                if item.project_role == "ORGANIZADOR"
            ]
            if len(organizers) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El proyecto debe conservar al menos un organizador",
                )
        removed_user_id = member.user_id
        removed_member_id = member.id
        self.members.delete(member)
        self.audit.record(
            module="proyectos_colaboracion",
            action="REMOVE_PROJECT_MEMBER",
            user_id=user_id,
            project_id=project_id,
            metadata={"member_id": str(member_id)},
        )
        self._activity_event(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_MEMBER_REMOVED",
            resource_type="project_member",
            resource_id=removed_member_id,
            summary_key="activity.member_removed",
            payload={"member_id": str(removed_member_id)},
        )
        NotificationService(self.db).record(
            DomainNotificationEvent(
                type="PROJECT_MEMBER_REMOVED",
                category="access",
                title="Acceso retirado",
                body="Ya no formas parte de este proyecto.",
                recipient_user_ids={removed_user_id},
                dedup_entity_id=removed_member_id,
                project_id=project_id,
                actor_user_id=user_id,
                resource_type="project",
                resource_id=project_id,
                deep_link=NotificationDeepLink(route_name="projects"),
            )
        )
        self.db.commit()
        return removed_user_id

    def set_permission(
        self, project_id: UUID, member_id: UUID, payload: PermissionRequest, user_id: UUID
    ) -> ProjectPermission:
        if payload.permission_code not in PERMISSION_CODES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_PERMISSION_CODE",
                    "message": f"Código de permiso no válido: {payload.permission_code}",
                },
            )
        ensure_project_permission(self.db, project_id, user_id, "members.manage")
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
        self,
        project_id: UUID,
        payload: VersionCreateRequest,
        user_id: UUID,
        idempotency_key: str | None = None,
    ) -> ProjectVersion:
        project = self.mutations.acquire(project_id)
        ensure_project_permission(self.db, project_id, user_id, "versions.create")
        if (
            payload.expected_project_revision is not None
            and payload.expected_project_revision != project.revision
        ):
            self._domain_error(
                409, "PROJECT_REVISION_CONFLICT", "El proyecto cambio antes de guardar la version"
            )
        if idempotency_key:
            existing = self.db.scalar(
                select(ProjectVersion).where(
                    ProjectVersion.project_id == project_id,
                    ProjectVersion.created_by_user_id == user_id,
                    ProjectVersion.idempotency_key == idempotency_key,
                )
            )
            if existing:
                return existing
        snapshot = self._build_project_snapshot(project_id, user_id)
        snapshot_hash = snapshot_sha256(snapshot)
        previous = self.db.scalar(
            select(ProjectVersion)
            .where(
                ProjectVersion.project_id == project_id,
                ProjectVersion.kind == "manual",
            )
            .order_by(ProjectVersion.version_number.desc())
            .limit(1)
        )
        if previous and previous.snapshot_hash == snapshot_hash and not payload.allow_duplicate:
            self._domain_error(
                409, "VERSION_DUPLICATE_CONTENT", "No hay cambios desde la ultima version"
            )
        version = self._create_version_record(
            project=project,
            project_id=project_id,
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            snapshot={} if settings.nosql_consolidated_mode else snapshot,
            kind="manual",
            idempotency_key=idempotency_key,
        )
        self._activity_event(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_VERSION_CREATED",
            resource_type="project_version",
            resource_id=version.id,
            summary_key="activity.version_created",
            payload={"version_id": str(version.id), "version_number": version.version_number},
        )
        recipients = self._active_member_ids(project_id)
        NotificationService(self.db).record(
            DomainNotificationEvent(
                type="PROJECT_VERSION_CREATED",
                category="versions",
                title="Version de proyecto guardada",
                body=f"Se guardo la version {version.version_number}: {version.name}.",
                recipient_user_ids=recipients,
                dedup_entity_id=version.id,
                project_id=project_id,
                actor_user_id=user_id,
                severity="success",
                resource_type="project_version",
                resource_id=version.id,
                deep_link=NotificationDeepLink(
                    route_name="project_collaborative",
                    params={"project_id": str(project_id)},
                    query={"panel": "versions", "version_id": str(version.id)},
                ),
                push_default=False,
            )
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
        ensure_project_permission(self.db, project_id, user_id, "project.read")
        return [
            {
                **self._version_dict(version),
                "created_by_name": user_name,
            }
            for version, user_name in self.projects.list_versions(project_id)
        ]

    async def restore_preview(self, project_id: UUID, version_id: UUID, user_id: UUID) -> dict:
        project = ensure_project_exists(self.projects.get(project_id))
        ensure_project_permission(self.db, project_id, user_id, "project.read")
        version = self.projects.get_version(version_id)
        if version is None or version.project_id != project_id:
            self._domain_error(404, "VERSION_NOT_FOUND", "Version del proyecto no encontrada")
        raw_snapshot, warnings = await self._load_version_snapshot(version, project)
        snapshot = self._parse_snapshot(raw_snapshot, project)
        current = ProjectSnapshotV2.model_validate(
            self._build_project_snapshot(project_id, user_id)
        )
        target_stats = self._snapshot_stats(snapshot)
        current_stats = self._snapshot_stats(current)
        return {
            "version": self._version_dict(version),
            "current_revision": project.revision,
            "effective_schema_version": snapshot.schema_version,
            "summary": target_stats,
            "differences": {
                key: target_stats[key] - current_stats[key]
                for key in ("diagrams", "classes", "attributes", "methods", "relationships")
            },
            "warnings": [
                *warnings,
                *(["snapshot_v1_adapted"] if raw_snapshot.get("schema_version", 1) == 1 else []),
            ],
        }

    def list_changes(
        self,
        project_id: UUID,
        user_id: UUID,
        limit: int,
        after_sequence: int | None = None,
    ) -> list[dict]:
        ensure_project_exists(self.projects.get(project_id))
        self._require_member(project_id, user_id)
        records = (
            self.projects.list_changes_after(project_id, after_sequence, limit)
            if after_sequence is not None
            else self.projects.list_changes(project_id, limit)
        )
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
            for event, user_name in records
        ]

    def list_activity(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        before_sequence: int | None,
        limit: int,
        event_types: set[str] | None = None,
    ) -> dict:
        ensure_project_exists(self.projects.get(project_id))
        self._require_member(project_id, user_id)
        rows = self.projects.list_activity_before(project_id, before_sequence, limit, event_types)
        has_more = len(rows) > limit
        visible = rows[:limit]
        items = [self._event_dict(event, user_name) for event, user_name in visible]
        return {
            "items": items,
            "next_cursor": items[-1]["sequence_number"] if has_more and items else None,
            "has_more": has_more,
            "latest_sequence": self.projects.current_event_sequence(project_id),
        }

    async def restore_version(
        self,
        project_id: UUID,
        version_id: UUID,
        user_id: UUID,
        *,
        idempotency_key: str,
        payload: RestoreRequest | None = None,
    ) -> dict:
        project = self.mutations.acquire(project_id)
        ensure_project_permission(self.db, project_id, user_id, "versions.restore")
        version = self.projects.get_version(version_id)
        if version is None or version.project_id != project.id:
            self._domain_error(404, "VERSION_NOT_FOUND", "Version del proyecto no encontrada")
        existing_operation = self.db.scalar(
            select(ProjectRestoreOperation).where(
                ProjectRestoreOperation.project_id == project_id,
                ProjectRestoreOperation.requested_by_user_id == user_id,
                ProjectRestoreOperation.idempotency_key == idempotency_key,
            )
        )
        if existing_operation:
            if existing_operation.source_version_id != version_id:
                self._domain_error(
                    409, "IDEMPOTENCY_KEY_REUSED", "La clave ya se uso para otra version"
                )
            if existing_operation.status != "completed":
                self._domain_error(409, "RESTORE_IN_PROGRESS", "La restauracion ya esta en curso")
            backup = self.projects.get_version(existing_operation.backup_version_id)
            restored_ids = [
                UUID(value)
                for value in existing_operation.diagnostics_json.get("restored_diagram_ids", [])
            ]
            return self._restore_result(
                existing_operation,
                version,
                backup,
                restored_ids,
                idempotent_replay=True,
            )
        if (
            payload
            and payload.expected_project_revision is not None
            and payload.expected_project_revision != project.revision
        ):
            self._domain_error(
                409, "PROJECT_REVISION_CONFLICT", "El proyecto cambio antes de restaurar"
            )
        raw_snapshot, _ = await self._load_version_snapshot(version, project)
        snapshot = self._parse_snapshot(raw_snapshot, project)
        before_snapshot = self._build_project_snapshot(project_id, user_id)
        before_hash = snapshot_sha256(before_snapshot)
        operation = ProjectRestoreOperation(
            project_id=project_id,
            source_version_id=version.id,
            requested_by_user_id=user_id,
            idempotency_key=idempotency_key,
            status="validating",
            source_snapshot_hash=snapshot_sha256(snapshot),
            before_snapshot_hash=before_hash,
            project_revision_before=project.revision,
            diagnostics_json={},
            started_at=datetime.now(UTC),
        )
        self.db.add(operation)
        self.db.flush()

        backup = self._create_version_record(
            project=project,
            project_id=project_id,
            user_id=user_id,
            name=f"Respaldo antes de restaurar v{version.version_number}",
            description="Snapshot automatico de seguridad previo a la restauracion.",
            snapshot=before_snapshot,
            kind="pre_restore_backup",
            metadata={
                "restore_operation_id": str(operation.id),
                "source_version_id": str(version.id),
            },
        )
        operation.backup_version_id = backup.id
        from app.modules.modelado_uml.services.uml_service import UmlService

        restored_ids = UmlService(self.db).restore_project_snapshot(
            project_id, snapshot.model_dump(mode="json"), user_id
        )
        self._restore_snapshot_settings(project, snapshot, user_id)
        project.revision += 1
        mark_uml_project_for_sync(self.db, project_id)
        after_snapshot = self._build_project_snapshot(project_id, user_id)
        operation.status = "completed"
        operation.after_snapshot_hash = snapshot_sha256(after_snapshot)
        operation.project_revision_after = project.revision
        operation.diagnostics_json = {
            "restored_diagram_ids": [str(item) for item in restored_ids],
        }
        operation.completed_at = datetime.now(UTC)
        from app.core.config.settings import settings
        from app.core.nosql.contracts import AiMessageDocument
        from app.modules.asistente_proyecto.models import AiMessage
        from app.modules.asistente_proyecto.repositories.assistant_repository import (
            AssistantRepository,
        )
        from app.modules.asistente_proyecto.services.conversation_document_store import (
            SyncConversationDocumentStore,
            enqueue_message_document,
            message_content_hash,
        )

        conversation = AssistantRepository(self.db).get_conversation(project_id, for_update=True)
        if conversation is not None:
            conversation.last_message_sequence += 1
            message_values = {
                "conversation_id": conversation.id,
                "project_id": project_id,
                "author_user_id": None,
                "role": "system",
                "content": f"El proyecto fue restaurado a la version {version.version_number}.",
                "sequence_number": conversation.last_message_sequence,
                "client_message_id": None,
                "correlation_id": operation.id,
                "status": "completed",
                "detected_intents": [],
                "references_json": [
                    {
                        "type": "project_version",
                        "id": str(version.id),
                        "label": f"Version {version.version_number}",
                    }
                ],
                "metadata_json": {"restore_operation_id": str(operation.id)},
            }
            if settings.nosql_consolidated_mode:
                system_message = AiMessageDocument(
                    _id=uuid4(), content_hash="0" * 64, **message_values
                )
                system_message.content_hash = message_content_hash(system_message)
                SyncConversationDocumentStore().upsert(system_message)
            else:
                system_message = AiMessage(**message_values)
                self.db.add(system_message)
                enqueue_message_document(self.db, system_message)
        restore_event = self._activity_event(
            project_id=project_id,
            user_id=user_id,
            event_type="PROJECT_VERSION_RESTORED",
            resource_type="project_restore_operation",
            resource_id=operation.id,
            correlation_id=operation.id,
            summary_key="activity.version_restored",
            payload={
                "source_version_id": str(version.id),
                "source_version_number": version.version_number,
                "backup_version_id": str(backup.id),
                "backup_version_number": backup.version_number,
                "project_revision": project.revision,
            },
        )
        NotificationService(self.db).record(
            DomainNotificationEvent(
                type="PROJECT_VERSION_RESTORED",
                category="versions",
                title="Proyecto restaurado",
                body=f"El proyecto fue restaurado a la version {version.version_number}.",
                recipient_user_ids=self._active_member_ids(project_id),
                dedup_entity_id=operation.id,
                project_id=project_id,
                actor_user_id=user_id,
                severity="warning",
                resource_type="project_restore_operation",
                resource_id=operation.id,
                deep_link=NotificationDeepLink(
                    route_name="project_collaborative",
                    params={"project_id": str(project_id)},
                    query={"panel": "versions", "version_id": str(version.id)},
                ),
            )
        )
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
        return self._restore_result(operation, version, backup, restored_ids, restore_event)

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
        existing = self.projects.get_event_by_client_id(project_id, user_id, client_event_id)
        if existing is not None:
            return existing, False
        project = self.mutations.acquire(project_id)
        event = CollaborationEvent(
            project_id=project_id,
            diagram_id=diagram_id,
            user_id=user_id,
            client_event_id=client_event_id,
            sequence_number=self.projects.next_event_sequence(project_id),
            event_type=EVENT_ALIASES.get(event_type, event_type),
            element_type=element_type,
            element_id=element_id,
            base_version=base_version,
            payload=payload,
            resource_type=element_type,
            resource_id=element_id,
            correlation_id=_optional_uuid(payload.get("correlation_id")),
            summary_key=f"activity.{EVENT_ALIASES.get(event_type, event_type).casefold()}",
        )
        project.revision += 1
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event, True

    @staticmethod
    def _event_dict(event: CollaborationEvent, user_name: str) -> dict:
        return {
            "id": event.id,
            "project_id": event.project_id,
            "diagram_id": event.diagram_id,
            "user_id": event.user_id,
            "user_name": event.actor_display_name or user_name,
            "client_event_id": event.client_event_id,
            "sequence_number": event.sequence_number,
            "event_type": event.event_type,
            "element_type": event.element_type,
            "element_id": event.element_id,
            "base_version": event.base_version,
            "payload": event.payload,
            "created_at": event.created_at,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
            "summary_key": event.summary_key,
        }

    def _create_version_record(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None,
        snapshot: dict,
        project: Project | None = None,
        kind: str = "manual",
        idempotency_key: str | None = None,
        metadata: dict | None = None,
    ) -> ProjectVersion:
        project = project or self.mutations.acquire(project_id)
        parsed = ProjectSnapshotV2.model_validate(snapshot)
        canonical = canonicalize_project_snapshot(parsed)
        if len(canonical) > settings.project_snapshot_max_bytes:
            self._domain_error(
                413, "SNAPSHOT_TOO_LARGE", "El snapshot excede el limite configurado"
            )
        version = ProjectVersion(
            project_id=project_id,
            created_by_user_id=user_id,
            version_number=project.next_version_number,
            name=name,
            description=description,
            snapshot=snapshot,
            status="available",
            kind=kind,
            snapshot_schema_version=parsed.schema_version,
            snapshot_hash=snapshot_sha256(parsed),
            snapshot_size_bytes=len(canonical),
            project_revision=project.revision,
            idempotency_key=idempotency_key,
            metadata_json=metadata or {},
        )
        project.next_version_number += 1
        self.db.add(version)
        self.db.flush()
        diagram_id = self._snapshot_diagram_id(snapshot, project_id)
        if settings.nosql_consolidated_mode:
            persist_version_document(version, diagram_id=diagram_id, content=snapshot)
        else:
            enqueue_version_document(self.db, version, diagram_id=diagram_id)
        return version

    def _snapshot_diagram_id(self, snapshot: dict, project_id: UUID) -> UUID:
        for item in snapshot.get("diagrams", []):
            diagram_id = _optional_uuid(item.get("id"))
            if diagram_id is not None:
                return diagram_id
        diagram_id = self.db.scalar(
            select(UmlDiagram.id)
            .where(UmlDiagram.project_id == project_id)
            .order_by(UmlDiagram.created_at, UmlDiagram.id)
            .limit(1)
        )
        if diagram_id is None:
            self._domain_error(
                409,
                "PROJECT_DIAGRAM_MISSING",
                "El proyecto no tiene un diagrama asociado para versionar",
            )
        return diagram_id

    async def _load_version_snapshot(
        self, version: ProjectVersion, project: Project
    ) -> tuple[dict, list[str]]:
        warnings: list[str] = []
        try:
            document = await self.version_documents.safe_get(version.id)
        except (MongoUnavailableError, PyMongoError):
            self._domain_error(
                503,
                "VERSION_DOCUMENT_UNAVAILABLE",
                "El almacenamiento documental de versiones no esta disponible",
            )
        if document is None:
            if not settings.uml_versions_sql_fallback_enabled:
                self._domain_error(
                    503,
                    "VERSION_DOCUMENT_UNAVAILABLE",
                    "El snapshot documental no esta disponible",
                )
            return dict(version.snapshot), ["mongodb_snapshot_fallback_sql"]

        registry_hash = version.snapshot_hash if len(version.snapshot_hash or "") == 64 else ""
        document_valid = (
            document.project_id == project.id
            and document.version_number == version.version_number
            and document.content_hash == registry_hash
        )
        if document_valid:
            try:
                parsed = self._parse_snapshot(document.content, project)
                document_valid = snapshot_sha256(parsed) == document.content_hash
            except HTTPException:
                document_valid = False

        if settings.uml_versions_compare_reads:
            sql_parsed = self._parse_snapshot(version.snapshot, project)
            effective_sql_hash = snapshot_sha256(sql_parsed)
        else:
            effective_sql_hash = registry_hash
        if settings.uml_versions_compare_reads and effective_sql_hash != document.content_hash:
            document_valid = False
            logger.error(
                "UML version SQL/MongoDB hash divergence",
                extra={"version_id": str(version.id), "project_id": str(project.id)},
            )

        if document_valid:
            return dict(document.content), warnings
        if settings.uml_versions_sql_fallback_enabled:
            warnings.append("mongodb_snapshot_hash_mismatch_fallback_sql")
            return dict(version.snapshot), warnings
        self._domain_error(
            409,
            "VERSION_DOCUMENT_DIVERGED",
            "El snapshot documental no coincide con su registro relacional",
        )
        raise AssertionError("unreachable")

    def _build_project_snapshot(self, project_id: UUID, user_id: UUID) -> dict:
        from app.modules.asistente_proyecto.repositories.assistant_repository import (
            AssistantRepository,
        )
        from app.modules.generacion_software.repositories.theme_repository import ThemeRepository
        from app.modules.modelado_uml.services.uml_service import UmlService

        project = ensure_project_exists(self.projects.get(project_id))
        uml_service = UmlService(self.db)
        diagrams = uml_service.uml.list_diagrams_by_project(project_id)
        theme = ThemeRepository(self.db).get(project_id)
        ai_settings = AssistantRepository(self.db).get_settings(project_id)
        snapshot = ProjectSnapshotV2(
            captured_at=datetime.now(UTC),
            project=SnapshotProject(
                id=project.id,
                name=project.name,
                description=project.description,
            ),
            diagrams=[
                uml_service._build_internal_model(diagram).model_dump(mode="json")
                for diagram in diagrams
            ],
            flutter_theme=(
                SnapshotFlutterTheme(
                    config=theme.config_json,
                    preset_name=theme.preset_name,
                    schema_version=theme.schema_version,
                    revision=theme.revision,
                )
                if theme
                else None
            ),
            generation_settings=project.settings.get("generation_settings", {}),
            ai_settings=(
                SnapshotAiSettings(
                    enabled=ai_settings.enabled,
                    preferred_provider=ai_settings.preferred_provider,
                    model_name=ai_settings.model_name,
                    fallback_enabled=ai_settings.fallback_enabled,
                    require_confirmation=ai_settings.require_confirmation,
                )
                if ai_settings
                else None
            ),
        )
        return snapshot.model_dump(mode="json")

    def _restore_snapshot_settings(
        self,
        project: Project,
        snapshot: ProjectSnapshotV2,
        user_id: UUID,
    ) -> None:
        from app.modules.asistente_proyecto.models import AiProjectSettings
        from app.modules.asistente_proyecto.repositories.assistant_repository import (
            AssistantRepository,
        )
        from app.modules.generacion_software.models import FlutterThemeSettings
        from app.modules.generacion_software.repositories.theme_repository import ThemeRepository

        project.name = snapshot.project.name
        project.description = snapshot.project.description
        project.settings = {
            **project.settings,
            "generation_settings": snapshot.generation_settings,
        }
        themes = ThemeRepository(self.db)
        existing_theme = themes.get(project.id)
        if snapshot.flutter_theme:
            theme_values = snapshot.flutter_theme
            if existing_theme is None:
                themes.add(
                    FlutterThemeSettings(
                        project_id=project.id,
                        config_json=theme_values.config.model_dump(),
                        preset_name=theme_values.preset_name,
                        schema_version=theme_values.schema_version,
                        revision=theme_values.revision,
                        created_by_user_id=user_id,
                        updated_by_user_id=user_id,
                    )
                )
            else:
                existing_theme.config_json = theme_values.config.model_dump()
                existing_theme.preset_name = theme_values.preset_name
                existing_theme.schema_version = theme_values.schema_version
                existing_theme.revision = max(existing_theme.revision + 1, theme_values.revision)
                existing_theme.updated_by_user_id = user_id
        assistant = AssistantRepository(self.db)
        existing_ai = assistant.get_settings(project.id)
        if snapshot.ai_settings:
            ai_values = snapshot.ai_settings.model_dump()
            if existing_ai is None:
                self.db.add(
                    AiProjectSettings(
                        project_id=project.id,
                        **ai_values,
                        settings_json={},
                        created_by_user_id=user_id,
                        updated_by_user_id=user_id,
                    )
                )
            else:
                for key, value in ai_values.items():
                    setattr(existing_ai, key, value)
                existing_ai.updated_by_user_id = user_id

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
            "kind": version.kind,
            "snapshot_schema_version": version.snapshot_schema_version,
            "snapshot_hash": version.snapshot_hash,
            "snapshot_size_bytes": version.snapshot_size_bytes,
            "project_revision": version.project_revision,
        }

    def _ensure_version_manager(self, project: Project, user_id: UUID) -> None:
        if project.owner_id == user_id:
            return
        member = self.members.get_membership(project.id, user_id)
        if member is None or member.project_role != "ORGANIZADOR":
            self._domain_error(
                403, "VERSION_MANAGE_FORBIDDEN", "Se requiere ser propietario u organizador"
            )

    @staticmethod
    def _domain_error(http_status: int, code: str, message: str) -> None:
        raise HTTPException(status_code=http_status, detail={"code": code, "message": message})

    def _parse_snapshot(self, raw: dict, project: Project) -> ProjectSnapshotV2:
        try:
            if raw.get("schema_version", 1) == 1:
                current = ProjectSnapshotV2.model_validate(
                    self._build_project_snapshot(project.id, project.owner_id)
                )
                upgraded, _ = upgrade_snapshot_v1_to_v2(
                    raw,
                    SnapshotProject(
                        id=project.id, name=project.name, description=project.description
                    ),
                    generation_settings=current.generation_settings,
                    flutter_theme=current.flutter_theme,
                    ai_settings=current.ai_settings,
                )
                return upgraded
            return parse_project_snapshot(
                raw,
                SnapshotProject(id=project.id, name=project.name, description=project.description),
            )
        except (ValueError, ValidationError) as exc:
            code = (
                "SNAPSHOT_VERSION_UNSUPPORTED" if "no soportada" in str(exc) else "SNAPSHOT_INVALID"
            )
            self._domain_error(409 if code.endswith("UNSUPPORTED") else 422, code, str(exc))
        raise AssertionError("unreachable")

    def _active_member_ids(self, project_id: UUID) -> set[UUID]:
        return set(
            self.db.scalars(
                select(ProjectMember.user_id).where(ProjectMember.project_id == project_id)
            )
        )

    def _activity_event(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        event_type: str,
        resource_type: str,
        resource_id: UUID,
        summary_key: str,
        payload: dict,
        correlation_id: UUID | None = None,
    ) -> CollaborationEvent:
        event = CollaborationEvent(
            project_id=project_id,
            diagram_id=None,
            user_id=user_id,
            client_event_id=uuid4(),
            sequence_number=self.projects.next_event_sequence(project_id),
            event_type=event_type,
            element_type=resource_type,
            element_id=resource_id,
            base_version=None,
            payload=payload,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            summary_key=summary_key,
        )
        self.db.add(event)
        self.db.flush()
        return event

    @staticmethod
    def _snapshot_stats(snapshot: ProjectSnapshotV2) -> dict[str, int]:
        totals = {
            "diagrams": len(snapshot.diagrams),
            "classes": 0,
            "attributes": 0,
            "methods": 0,
            "relationships": 0,
        }
        for diagram in snapshot.diagrams:
            classes = diagram.get("classes", [])
            totals["classes"] += len(classes)
            totals["attributes"] += sum(len(item.get("attributes", [])) for item in classes)
            totals["methods"] += sum(len(item.get("methods", [])) for item in classes)
            totals["relationships"] += len(diagram.get("relationships", []))
        return totals

    def _restore_result(
        self,
        operation: ProjectRestoreOperation,
        version: ProjectVersion,
        backup: ProjectVersion | None,
        restored_ids: list[UUID],
        event: CollaborationEvent | None = None,
        *,
        idempotent_replay: bool = False,
    ) -> dict:
        if backup is None:
            self._domain_error(409, "RESTORE_FAILED", "No se encontro el respaldo de restauracion")
        return {
            "restored_version": self._version_dict(version),
            "backup_version": self._version_dict(backup),
            "restored_diagram_ids": restored_ids,
            "restore_operation_id": operation.id,
            "project_revision": operation.project_revision_after
            or operation.project_revision_before,
            "event_sequence": event.sequence_number if event else None,
            "event_id": event.id if event else None,
            "client_event_id": event.client_event_id if event else None,
            "idempotent_replay": idempotent_replay,
        }

    def _require_member(self, project_id: UUID, user_id: UUID) -> ProjectMember:
        from app.modules.proyectos_colaboracion.validators.project_validator import (
            ensure_membership,
        )

        return ensure_membership(self.members.get_membership(project_id, user_id))
