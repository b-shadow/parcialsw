"""Router para el registro de cambios (Change Log NoSQL)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.changelog.contratos import PaginaRegistroCambios
from app.core.changelog.servicio import ServicioRegistroCambios
from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.proyectos_colaboracion.repositories.repositorio_integrantes import (
    RepositorioIntegrantes,
)
from app.modules.proyectos_colaboracion.validators.validador_proyecto import asegurar_participacion

router = APIRouter(prefix="/projects", tags=["registro-cambios"])


@router.get("/{project_id}/change-log", response_model=PaginaRegistroCambios)
def listar_registro_cambios(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    before_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    actor_id: UUID | None = None,
    entity_type: str | None = None,
) -> PaginaRegistroCambios:
    asegurar_participacion(RepositorioIntegrantes(db).obtener_participacion(project_id, current_user.id))
    service = ServicioRegistroCambios()
    page = service.listar_proyecto(
        project_id,
        db=db,
        before_id=before_id,
        limit=limit,
        actor_id=actor_id,
        entity_type=entity_type,
    )
    return service.resolver_nombres(db, page)
