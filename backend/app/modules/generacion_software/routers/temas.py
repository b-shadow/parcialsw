from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.asistente_proyecto.services.publicador_eventos import PublicadorEventosIAProyecto
from app.modules.generacion_software.schemas.temas import (
    ActualizacionTemaFlutter,
    AplicacionTemaFlutterPredefinido,
    EscrituraTemaFlutterPredefinido,
    MutacionTemaFlutter,
    RespuestaTemaFlutter,
    RespuestaTemaFlutterPredefinido,
    RespuestaValidacionTemaFlutter,
    SolicitudValidacionTemaFlutter,
)
from app.modules.generacion_software.services.servicio_temas import ServicioTemas

router = APIRouter(prefix="/projects", tags=["flutter-theme"])


def _revision_actual(if_match: str | None, if_none_match: str | None = None) -> int | None:
    if if_none_match == "*":
        return 0
    if not if_match:
        return None
    value = if_match.strip().strip('"')
    prefix = "flutter-theme-revision-"
    return int(value[len(prefix):]) if value.startswith(prefix) and value[len(prefix):].isdigit() else None


def _etiqueta_etag(response: Response, revision: int) -> None:
    response.headers["ETag"] = f'"flutter-theme-revision-{revision}"'


async def _publish(project_id: UUID, user: Usuario, revision: int) -> None:
    await PublicadorEventosIAProyecto().publicar_persistido(
        project_id=project_id, actor_user_id=user.id, event_type="FLUTTER_THEME_UPDATED",
        payload={"revision": revision}, correlation_id=uuid4(),
    )


@router.get("/{project_id}/flutter-theme", response_model=RespuestaTemaFlutter)
def obtener_tema_flutter(project_id: UUID, response: Response,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)], db: Annotated[Session, Depends(obtener_sesion_bd)]) -> RespuestaTemaFlutter:
    result = ServicioTemas(db).get(project_id, current_user.id)
    _etiqueta_etag(response, result.revision)
    return result


@router.put("/{project_id}/flutter-theme", response_model=RespuestaTemaFlutter)
async def guardar_tema_flutter(project_id: UUID, payload: ActualizacionTemaFlutter, response: Response,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)], db: Annotated[Session, Depends(obtener_sesion_bd)],
    if_match: Annotated[str | None, Header()] = None,
    if_none_match: Annotated[str | None, Header()] = None) -> RespuestaTemaFlutter:
    expected_revision = _revision_actual(if_match, if_none_match)
    result = ServicioTemas(db).put(project_id, payload, current_user.id, expected_revision)
    _etiqueta_etag(response, result.revision)
    if expected_revision != result.revision:
        await _publish(project_id, current_user, result.revision)
    return result


@router.post("/{project_id}/flutter-theme/validate", response_model=RespuestaValidacionTemaFlutter)
def validar_tema_flutter(project_id: UUID, payload: SolicitudValidacionTemaFlutter,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)], db: Annotated[Session, Depends(obtener_sesion_bd)]) -> RespuestaValidacionTemaFlutter:
    return ServicioTemas(db).validate(project_id, payload.config, current_user.id)


@router.post("/{project_id}/flutter-theme/reset", response_model=RespuestaTemaFlutter)
async def restablecer_tema_flutter(project_id: UUID, payload: MutacionTemaFlutter, response: Response,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)], db: Annotated[Session, Depends(obtener_sesion_bd)],
    if_match: Annotated[str | None, Header()] = None) -> RespuestaTemaFlutter:
    expected_revision = payload.expected_revision if payload.expected_revision is not None else _revision_actual(if_match)
    result = ServicioTemas(db).reset(project_id, current_user.id, expected_revision)
    _etiqueta_etag(response, result.revision)
    if expected_revision != result.revision:
        await _publish(project_id, current_user, result.revision)
    return result


@router.get("/{project_id}/flutter-theme/presets", response_model=list[RespuestaTemaFlutterPredefinido])
def listar_temas_flutter_predefinidos(project_id: UUID, current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)]) -> list[RespuestaTemaFlutterPredefinido]:
    return ServicioTemas(db).listar_predefinidos(project_id, current_user.id)


@router.post("/{project_id}/flutter-theme/presets", response_model=RespuestaTemaFlutterPredefinido, status_code=status.HTTP_201_CREATED)
def crear_tema_flutter_predefinido(project_id: UUID, payload: EscrituraTemaFlutterPredefinido,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)], db: Annotated[Session, Depends(obtener_sesion_bd)]) -> RespuestaTemaFlutterPredefinido:
    return ServicioTemas(db).crear_predefinido(project_id, payload, current_user.id)


@router.put("/{project_id}/flutter-theme/presets/{preset_id}", response_model=RespuestaTemaFlutterPredefinido)
def actualizar_tema_flutter_predefinido(project_id: UUID, preset_id: UUID, payload: EscrituraTemaFlutterPredefinido,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)], db: Annotated[Session, Depends(obtener_sesion_bd)]) -> RespuestaTemaFlutterPredefinido:
    return ServicioTemas(db).actualizar_predefinido(project_id, preset_id, payload, current_user.id)


@router.delete("/{project_id}/flutter-theme/presets/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tema_flutter_predefinido(project_id: UUID, preset_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)], db: Annotated[Session, Depends(obtener_sesion_bd)]) -> None:
    ServicioTemas(db).eliminar_predefinido(project_id, preset_id, current_user.id)


@router.post("/{project_id}/flutter-theme/presets/{preset_id}/apply", response_model=RespuestaTemaFlutter)
async def aplicar_tema_flutter_predefinido(project_id: UUID, preset_id: str, payload: AplicacionTemaFlutterPredefinido,
    response: Response, current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)]) -> RespuestaTemaFlutter:
    result = ServicioTemas(db).aplicar_predefinido(project_id, preset_id, current_user.id, payload.expected_revision)
    _etiqueta_etag(response, result.revision)
    if payload.expected_revision != result.revision:
        await _publish(project_id, current_user, result.revision)
    return result
