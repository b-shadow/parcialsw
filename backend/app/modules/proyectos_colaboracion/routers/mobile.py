from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.proyectos_colaboracion.schemas.mobile import (
    MobileDiagramDetail,
    MobileDiagramSummary,
    MobileGenerationSummary,
    MobileProjectSummary,
)
from app.modules.proyectos_colaboracion.services.mobile_service import MobileReadService

router = APIRouter(prefix="/mobile", tags=["mobile-read"])


@router.get("/projects", response_model=list[MobileProjectSummary])
def list_mobile_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[MobileProjectSummary]:
    return MobileReadService(db).list_projects(current_user.id)


@router.get("/projects/{project_id}/diagrams", response_model=list[MobileDiagramSummary])
def list_mobile_diagrams(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[MobileDiagramSummary]:
    return MobileReadService(db).list_diagrams(project_id, current_user.id)


@router.get("/diagrams/{diagram_id}", response_model=MobileDiagramDetail)
def get_mobile_diagram(
    diagram_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MobileDiagramDetail:
    return MobileReadService(db).get_diagram(diagram_id, current_user.id)


@router.get(
    "/projects/{project_id}/generations",
    response_model=list[MobileGenerationSummary],
)
def list_mobile_generations(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=30, ge=1, le=100),
) -> list[MobileGenerationSummary]:
    return MobileReadService(db).list_generations(project_id, current_user.id, limit)

