from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.asistente_proyecto.schemas import (
    ActualizacionConfiguracionIAProyecto,
    ActualizacionConversacionIA,
    ActualizacionEstadoRecomendacionIA,
    CreacionConversacionIA,
    EstadoProveedorIA,
    PaginaMensajesIA,
    RespuestaAccionIA,
    RespuestaConfiguracionIAProyecto,
    RespuestaConversacionIA,
    RespuestaDecisionAccionIA,
    RespuestaInteraccionIA,
    RespuestaRecomendacionIA,
    SolicitudInteraccionIA,
)
from app.modules.asistente_proyecto.services import (
    ServicioAplicacionIAProyecto,
    ServicioContratoAsistente,
    ServicioEjecucionAccionesIA,
)
from app.modules.asistente_proyecto.services.publicador_eventos import PublicadorEventosIAProyecto
from app.modules.asistente_proyecto.services.servicio_memoria_conversacion import (
    resumir_conversacion_proyecto,
)

router = APIRouter(prefix="/projects", tags=["asistente-proyecto"])


@router.post("/{project_id}/ai/interactions", response_model=RespuestaInteraccionIA)
async def crear_interaccion_ia(
    project_id: UUID,
    payload: SolicitudInteraccionIA,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    background_tasks: BackgroundTasks,
):
    response = await ServicioAplicacionIAProyecto(db).interactuar(project_id, current_user.id, payload)
    background_tasks.add_task(
        resumir_conversacion_proyecto, project_id, current_user.id, payload.conversation_id
    )
    return response


@router.get("/{project_id}/ai/provider-health", response_model=EstadoProveedorIA)
async def obtener_estado_proveedor_ia(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    return await ServicioAplicacionIAProyecto(db).estado_proveedor(project_id, current_user.id)


@router.post(
    "/{project_id}/ai/actions/{action_id}/confirm",
    response_model=RespuestaDecisionAccionIA,
)
async def confirmar_accion_ia(
    project_id: UUID,
    action_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    action, idempotent = ServicioEjecucionAccionesIA(db).confirmar(
        project_id, action_id, current_user.id
    )
    if not idempotent:
        publisher = PublicadorEventosIAProyecto()
        await publisher.publicar_persistido(
            project_id=project_id,
            actor_user_id=current_user.id,
            event_type="AI_ACTION_STATUS_CHANGED",
            payload=RespuestaAccionIA.model_validate(action).model_dump(mode="json"),
            correlation_id=uuid4(),
            conversation_sequence=None,
        )
        plan = action.payload.get("_plan") or {}
        diagram_id = UUID(plan["diagram_id"]) if plan.get("diagram_id") else None
        if diagram_id and action.action_type not in {
            "save_version", "prepare_backend_generation", "prepare_flutter_generation"
        }:
            await publisher.publicar_persistido(
                project_id=project_id,
                actor_user_id=current_user.id,
                event_type="UML_EVENT",
                payload={
                    "event_type": "AI_UPDATE_DIAGRAM",
                    "action_id": str(action.id),
                    "action_type": action.action_type,
                },
                correlation_id=uuid4(),
                diagram_id=diagram_id,
                conversation_sequence=None,
            )
        if action.action_type == "update_method_specification":
            result = action.result_json or {}
            await publisher.publicar_persistido(
                project_id=project_id,
                actor_user_id=current_user.id,
                event_type=(
                    "METHOD_SPECIFICATION_CREATED"
                    if result.get("created")
                    else "METHOD_SPECIFICATION_UPDATED"
                ),
                payload={
                    "diagram_id": plan.get("diagram_id"),
                    "method_id": result.get("method_id") or str(action.target_id),
                    "class_id": result.get("class_id"),
                    "revision": result.get("revision"),
                    "changed_fields": [key for key in action.payload if key != "_plan"],
                },
                correlation_id=uuid4(),
                diagram_id=diagram_id,
                conversation_sequence=None,
            )
    return RespuestaDecisionAccionIA(action=action, idempotent=idempotent)


@router.post(
    "/{project_id}/ai/actions/{action_id}/reject",
    response_model=RespuestaDecisionAccionIA,
)
async def rechazar_accion_ia(
    project_id: UUID,
    action_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    action, idempotent = ServicioEjecucionAccionesIA(db).rechazar(project_id, action_id, current_user.id)
    if not idempotent:
        await PublicadorEventosIAProyecto().publicar_persistido(
            project_id=project_id,
            actor_user_id=current_user.id,
            event_type="AI_ACTION_STATUS_CHANGED",
            payload=RespuestaAccionIA.model_validate(action).model_dump(mode="json"),
            correlation_id=uuid4(),
            conversation_sequence=None,
        )
    return RespuestaDecisionAccionIA(action=action, idempotent=idempotent)


@router.get("/{project_id}/ai/settings", response_model=RespuestaConfiguracionIAProyecto)
def obtener_configuracion_ia(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    return ServicioContratoAsistente(db).obtener_configuracion(project_id, current_user.id)


@router.put("/{project_id}/ai/settings", response_model=RespuestaConfiguracionIAProyecto)
def actualizar_configuracion_ia(
    project_id: UUID,
    payload: ActualizacionConfiguracionIAProyecto,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    return ServicioContratoAsistente(db).actualizar_configuracion(project_id, current_user.id, payload)


@router.get("/{project_id}/ai/conversation", response_model=RespuestaConversacionIA)
def obtener_conversacion_ia(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    return ServicioContratoAsistente(db).obtener_conversacion(project_id, current_user.id)


@router.get(
    "/{project_id}/ai/conversations",
    response_model=list[RespuestaConversacionIA],
)
def listar_conversaciones_ia(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    service = ServicioContratoAsistente(db)
    conversations = service.listar_conversaciones(project_id, current_user.id)
    return conversations or [service.obtener_conversacion(project_id, current_user.id)]


@router.post(
    "/{project_id}/ai/conversations",
    response_model=RespuestaConversacionIA,
    status_code=201,
)
def crear_conversacion_ia(
    project_id: UUID,
    payload: CreacionConversacionIA,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    return ServicioContratoAsistente(db).crear_conversacion(project_id, current_user.id, payload)


@router.patch(
    "/{project_id}/ai/conversations/{conversation_id}",
    response_model=RespuestaConversacionIA,
)
def actualizar_conversacion_ia(
    project_id: UUID,
    conversation_id: UUID,
    payload: ActualizacionConversacionIA,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    return ServicioContratoAsistente(db).actualizar_conversacion(
        project_id, conversation_id, current_user.id, payload
    )


@router.get("/{project_id}/ai/messages", response_model=PaginaMensajesIA)
async def listar_mensajes_ia(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    before_sequence: int | None = Query(default=None, ge=1),
    after_sequence: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    conversation_id: Annotated[UUID | None, Query()] = None,
):
    return await ServicioContratoAsistente(db).listar_mensajes(
        project_id,
        current_user.id,
        before_sequence,
        after_sequence,
        limit,
        conversation_id,
    )


@router.get("/{project_id}/ai/actions", response_model=list[RespuestaAccionIA])
def listar_acciones_ia(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    action_status: str | None = Query(default=None, alias="status", max_length=30),
    limit: int = Query(default=50, ge=1, le=200),
    conversation_id: Annotated[UUID | None, Query()] = None,
):
    return ServicioContratoAsistente(db).listar_acciones(
        project_id, current_user.id, action_status, limit, conversation_id
    )


@router.get("/{project_id}/ai/actions/{action_id}", response_model=RespuestaAccionIA)
def obtener_accion_ia(
    project_id: UUID,
    action_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    return ServicioContratoAsistente(db).obtener_accion(project_id, action_id, current_user.id)


@router.get("/{project_id}/ai/recommendations", response_model=list[RespuestaRecomendacionIA])
def listar_recomendaciones_ia(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    item_status: str | None = Query(default=None, alias="status", max_length=30),
    severity: str | None = Query(default=None, max_length=20),
    limit: int = Query(default=50, ge=1, le=200),
    conversation_id: Annotated[UUID | None, Query()] = None,
):
    return ServicioContratoAsistente(db).listar_recomendaciones(
        project_id, current_user.id, item_status, severity, limit, conversation_id
    )


@router.patch(
    "/{project_id}/ai/recommendations/{recommendation_id}",
    response_model=RespuestaRecomendacionIA,
)
async def actualizar_recomendacion_ia(
    project_id: UUID,
    recommendation_id: UUID,
    payload: ActualizacionEstadoRecomendacionIA,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
):
    recommendation = ServicioContratoAsistente(db).actualizar_recomendacion(
        project_id, recommendation_id, current_user.id, payload
    )
    await PublicadorEventosIAProyecto().publicar_persistido(
        project_id=project_id,
        actor_user_id=current_user.id,
        event_type="AI_RECOMMENDATION_STATUS_CHANGED",
        payload=RespuestaRecomendacionIA.model_validate(recommendation).model_dump(mode="json"),
        correlation_id=uuid4(),
        conversation_sequence=None,
    )
    return recommendation
