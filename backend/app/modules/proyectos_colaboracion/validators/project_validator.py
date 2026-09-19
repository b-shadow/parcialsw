from fastapi import HTTPException, status

from app.modules.proyectos_colaboracion.models import Project, ProjectMember


def ensure_project_exists(project: Project | None) -> Project:
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


def ensure_membership(member: ProjectMember | None) -> ProjectMember:
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso al proyecto")
    return member


def ensure_organizer(member: ProjectMember | None) -> ProjectMember:
    member = ensure_membership(member)
    if member.project_role != "ORGANIZADOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol Organizador del proyecto",
        )
    return member

