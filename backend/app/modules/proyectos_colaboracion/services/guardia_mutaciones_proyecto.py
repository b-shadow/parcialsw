from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, object_session

from app.modules.proyectos_colaboracion.models import Proyecto


class GuardiaMutacionesProyecto:
    """Shared PostgreSQL row lock for every versionable project mutation."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def acquire(self, project_id: UUID, expected_revision: int | None = None) -> Proyecto:
        project = self.db.scalar(
            select(Proyecto).where(Proyecto.id == project_id).with_for_update()
        )
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROJECT_NOT_FOUND", "message": "Proyecto no encontrado"},
            )
        if expected_revision is not None and project.revision != expected_revision:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PROJECT_REVISION_CONFLICT",
                    "message": "El proyecto fue modificado por otra operacion",
                    "current_revision": project.revision,
                },
            )
        return project

    @staticmethod
    def avanzar(project: Proyecto) -> int:
        project.revision += 1
        session = object_session(project)
        if session is not None:
            from app.modules.modelado_uml.services.almacen_diagrama_activo import (
                marcar_proyecto_uml_para_sincronizar,
            )

            marcar_proyecto_uml_para_sincronizar(session, project.id)
        return project.revision
