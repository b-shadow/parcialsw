from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.proyectos_colaboracion.schemas.movil import (
    DetalleDiagramaMovil,
    ResumenDiagramaMovil,
    ResumenGeneracionMovil,
    ResumenProyectoMovil,
)
from app.modules.proyectos_colaboracion.services.servicio_movil import ServicioLecturaMovil

router = APIRouter(prefix="/mobile", tags=["mobile-read"])


@router.get("/projects", response_model=list[ResumenProyectoMovil])
def listar_proyectos_movil(
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[ResumenProyectoMovil]:
    return ServicioLecturaMovil(db).listar_proyectos(current_user.id)


@router.get("/projects/{project_id}/diagrams", response_model=list[ResumenDiagramaMovil])
def listar_diagramas_movil(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[ResumenDiagramaMovil]:
    return ServicioLecturaMovil(db).listar_diagramas(project_id, current_user.id)


@router.get("/diagrams/{diagram_id}", response_model=DetalleDiagramaMovil)
def obtener_diagrama_movil(
    diagram_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> DetalleDiagramaMovil:
    return ServicioLecturaMovil(db).obtener_diagrama(diagram_id, current_user.id)


@router.get(
    "/projects/{project_id}/generations",
    response_model=list[ResumenGeneracionMovil],
)
def listar_generaciones_movil(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    limit: int = Query(default=30, ge=1, le=100),
) -> list[ResumenGeneracionMovil]:
    return ServicioLecturaMovil(db).listar_generaciones(project_id, current_user.id, limit)
