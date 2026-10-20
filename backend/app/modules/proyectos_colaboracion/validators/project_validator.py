from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.proyectos_colaboracion.models import Project, ProjectMember, ProjectPermission
from app.modules.proyectos_colaboracion.permissions import (
    PERMISSION_CODES,
    ROLE_DEFAULTS,
    effective_permissions,
)


def ensure_project_exists(project: Project | None) -> Project:
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


def ensure_membership(member: ProjectMember | None) -> ProjectMember:
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Sin acceso al proyecto"},
        )
    return member


def member_permissions(db: Session, member: ProjectMember) -> frozenset[str]:
    """Calcula los permisos efectivos de un integrante."""
    role_val = getattr(member, "project_role", None)
    if isinstance(role_val, str) and role_val in ROLE_DEFAULTS:
        role = role_val
    else:
        role = "ORGANIZADOR"

    granted: list[str] = []
    perms_attr = getattr(member, "permissions", None)
    if isinstance(perms_attr, (list, tuple, set, frozenset)):
        granted = [
            getattr(p, "permission_code", str(p))
            for p in perms_attr
            if getattr(p, "is_allowed", True)
        ]
    elif perms_attr is None and hasattr(member, "id"):
        try:
            rows = db.scalars(
                select(ProjectPermission.permission_code).where(
                    ProjectPermission.member_id == member.id,
                    ProjectPermission.is_allowed.is_(True),
                )
            ).all()
            if isinstance(rows, (list, tuple, set)):
                granted = list(rows)
        except Exception:
            pass

    return effective_permissions(role, granted)


def ensure_project_permission(
    db: Session,
    project_id: UUID,
    user_id: UUID,
    code: str,
    member: ProjectMember | None = None,
) -> ProjectMember:
    """Carga membresía y permisos otorgados; si code ∉ effective_permissions -> 403."""
    if member is None:
        from app.modules.proyectos_colaboracion.repositories.member_repository import (
            MemberRepository,
        )

        member = MemberRepository(db).get_membership(project_id, user_id)

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "Sin acceso al proyecto",
                "permission": code,
            },
        )
    perms = member_permissions(db, member)
    if code not in perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": f"Se requiere el permiso '{code}' en el proyecto",
                "permission": code,
                "role": getattr(member, "project_role", "UNKNOWN"),
            },
        )
    return member


def ensure_organizer(member: ProjectMember | None) -> ProjectMember:
    member = ensure_membership(member)
    role_val = getattr(member, "project_role", None)
    role = role_val if isinstance(role_val, str) else "ORGANIZADOR"
    if "members.manage" not in ROLE_DEFAULTS.get(role, frozenset()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "Se requiere rol Organizador del proyecto",
                "permission": "members.manage",
                "role": role,
            },
        )
    return member
