from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.asistente_proyecto.services.event_publisher import ProjectAiEventPublisher
from app.modules.generacion_software.schemas.theme import (
    FlutterThemeMutation,
    FlutterThemePresetApply,
    FlutterThemePresetResponse,
    FlutterThemePresetWrite,
    FlutterThemeResponse,
    FlutterThemeUpdate,
    FlutterThemeValidationRequest,
    FlutterThemeValidationResponse,
)
from app.modules.generacion_software.services.theme_service import ThemeService

router = APIRouter(prefix="/projects", tags=["flutter-theme"])


def _revision(if_match: str | None, if_none_match: str | None = None) -> int | None:
    if if_none_match == "*":
        return 0
    if not if_match:
        return None
    value = if_match.strip().strip('"')
    prefix = "flutter-theme-revision-"
    return int(value[len(prefix):]) if value.startswith(prefix) and value[len(prefix):].isdigit() else None


def _etag(response: Response, revision: int) -> None:
    response.headers["ETag"] = f'"flutter-theme-revision-{revision}"'


async def _publish(project_id: UUID, user: User, revision: int) -> None:
    await ProjectAiEventPublisher().publish_persisted(
        project_id=project_id, actor_user_id=user.id, event_type="FLUTTER_THEME_UPDATED",
        payload={"revision": revision}, correlation_id=uuid4(),
    )


@router.get("/{project_id}/flutter-theme", response_model=FlutterThemeResponse)
def get_flutter_theme(project_id: UUID, response: Response,
    current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> FlutterThemeResponse:
    result = ThemeService(db).get(project_id, current_user.id)
    _etag(response, result.revision)
    return result


@router.put("/{project_id}/flutter-theme", response_model=FlutterThemeResponse)
async def put_flutter_theme(project_id: UUID, payload: FlutterThemeUpdate, response: Response,
    current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)],
    if_match: Annotated[str | None, Header()] = None,
    if_none_match: Annotated[str | None, Header()] = None) -> FlutterThemeResponse:
    expected_revision = _revision(if_match, if_none_match)
    result = ThemeService(db).put(project_id, payload, current_user.id, expected_revision)
    _etag(response, result.revision)
    if expected_revision != result.revision:
        await _publish(project_id, current_user, result.revision)
    return result


@router.post("/{project_id}/flutter-theme/validate", response_model=FlutterThemeValidationResponse)
def validate_flutter_theme(project_id: UUID, payload: FlutterThemeValidationRequest,
    current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> FlutterThemeValidationResponse:
    return ThemeService(db).validate(project_id, payload.config, current_user.id)


@router.post("/{project_id}/flutter-theme/reset", response_model=FlutterThemeResponse)
async def reset_flutter_theme(project_id: UUID, payload: FlutterThemeMutation, response: Response,
    current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)],
    if_match: Annotated[str | None, Header()] = None) -> FlutterThemeResponse:
    expected_revision = payload.expected_revision if payload.expected_revision is not None else _revision(if_match)
    result = ThemeService(db).reset(project_id, current_user.id, expected_revision)
    _etag(response, result.revision)
    if expected_revision != result.revision:
        await _publish(project_id, current_user, result.revision)
    return result


@router.get("/{project_id}/flutter-theme/presets", response_model=list[FlutterThemePresetResponse])
def list_flutter_theme_presets(project_id: UUID, current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]) -> list[FlutterThemePresetResponse]:
    return ThemeService(db).list_presets(project_id, current_user.id)


@router.post("/{project_id}/flutter-theme/presets", response_model=FlutterThemePresetResponse, status_code=status.HTTP_201_CREATED)
def create_flutter_theme_preset(project_id: UUID, payload: FlutterThemePresetWrite,
    current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> FlutterThemePresetResponse:
    return ThemeService(db).create_preset(project_id, payload, current_user.id)


@router.put("/{project_id}/flutter-theme/presets/{preset_id}", response_model=FlutterThemePresetResponse)
def update_flutter_theme_preset(project_id: UUID, preset_id: UUID, payload: FlutterThemePresetWrite,
    current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> FlutterThemePresetResponse:
    return ThemeService(db).update_preset(project_id, preset_id, payload, current_user.id)


@router.delete("/{project_id}/flutter-theme/presets/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flutter_theme_preset(project_id: UUID, preset_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> None:
    ThemeService(db).delete_preset(project_id, preset_id, current_user.id)


@router.post("/{project_id}/flutter-theme/presets/{preset_id}/apply", response_model=FlutterThemeResponse)
async def apply_flutter_theme_preset(project_id: UUID, preset_id: str, payload: FlutterThemePresetApply,
    response: Response, current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]) -> FlutterThemeResponse:
    result = ThemeService(db).apply_preset(project_id, preset_id, current_user.id, payload.expected_revision)
    _etag(response, result.revision)
    if payload.expected_revision != result.revision:
        await _publish(project_id, current_user, result.revision)
    return result
