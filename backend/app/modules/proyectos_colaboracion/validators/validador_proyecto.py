from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.proyectos_colaboracion.models import IntegranteProyecto, Proyecto
from app.modules.proyectos_colaboracion.permisos import (
    ROLE_DEFAULTS,
    permisos_efectivos,
)


def asegurar_proyecto_existente(project: Proyecto | None) -> Proyecto:
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


def asegurar_participacion(member: IntegranteProyecto | None) -> IntegranteProyecto:
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Sin acceso al proyecto"},
        )
    return member


def permisos_integrante(db: Session, member: IntegranteProyecto) -> frozenset[str]:
    """Calcula los permisos efectivos de un integrante."""
    role_val = getattr(member, "project_role", None)
    if isinstance(role_val, str) and role_val in ROLE_DEFAULTS:
        role = role_val
    else:
        role = "UNKNOWN"

    return permisos_efectivos(role)


def asegurar_permiso_proyecto(
    db: Session,
    project_id: UUID,
    user_id: UUID,
    code: str,
    member: IntegranteProyecto | None = None,
) -> IntegranteProyecto:
    """Carga membresía y comprueba los permisos fijos del rol."""
    if member is None:
        from app.modules.proyectos_colaboracion.repositories.repositorio_integrantes import (
            RepositorioIntegrantes,
        )

        member = RepositorioIntegrantes(db).obtener_participacion(project_id, user_id)

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "Sin acceso al proyecto",
                "permission": code,
            },
        )
    perms = permisos_integrante(db, member)
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


def asegurar_organizador(member: IntegranteProyecto | None) -> IntegranteProyecto:
    member = asegurar_participacion(member)
    role_val = getattr(member, "project_role", None)
    role = role_val if isinstance(role_val, str) else "UNKNOWN"
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
