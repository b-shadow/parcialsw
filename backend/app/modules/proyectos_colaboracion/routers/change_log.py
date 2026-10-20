"""Router para el registro de cambios (Change Log NoSQL)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.core.changelog.contracts import ChangeLogPage
from app.core.changelog.service import ChangeLogService
from app.modules.acceso_usuarios.models import User
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.validators.project_validator import ensure_membership

router = APIRouter(prefix="/projects", tags=["registro-cambios"])


@router.get("/{project_id}/change-log", response_model=ChangeLogPage)
def list_change_log(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    before_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    actor_id: UUID | None = None,
    entity_type: str | None = None,
) -> ChangeLogPage:
    ensure_membership(MemberRepository(db).get_membership(project_id, current_user.id))
    service = ChangeLogService()
    page = service.list_project(
        project_id,
        db=db,
        before_id=before_id,
        limit=limit,
        actor_id=actor_id,
        entity_type=entity_type,
    )
    return service.resolve_names(db, page)
