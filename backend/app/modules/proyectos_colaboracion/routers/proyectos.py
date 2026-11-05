from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.proyectos_colaboracion.models import IntegranteProyecto, Proyecto
from app.modules.proyectos_colaboracion.schemas.proyecto import (
    RespuestaCandidatoIntegranteProyecto,
    RespuestaEventoColaboracion,
    RespuestaIntegranteProyecto,
    RespuestaMiParticipacion,
    RespuestaPaginaActividad,
    RespuestaProyecto,
    RespuestaRestauracionVersion,
    RespuestaVersion,
    RespuestaVistaPreviaRestauracion,
    SolicitudActualizacionProyecto,
    SolicitudActualizarIntegrante,
    SolicitudAgregarIntegrante,
    SolicitudCreacionProyecto,
    SolicitudCreacionVersion,
    SolicitudRestauracion,
)
from app.modules.proyectos_colaboracion.services.servicio_proyectos import ServicioProyectos
from app.websocket.gestor_conexiones import manager

router = APIRouter(prefix="/projects", tags=["proyectos"])


@router.post("", response_model=RespuestaProyecto, status_code=status.HTTP_201_CREATED)
def crear_proyecto(
    payload: SolicitudCreacionProyecto,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> Proyecto:
    return ServicioProyectos(db).crear_proyecto(payload, current_user.id)


@router.get("", response_model=list[RespuestaProyecto])
def listar_proyectos(
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[Proyecto]:
    return ServicioProyectos(db).listar_proyectos(current_user.id)


@router.get("/{project_id}", response_model=RespuestaProyecto)
def obtener_proyecto(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> Proyecto:
    return ServicioProyectos(db).obtener_proyecto(project_id, current_user.id)


@router.patch("/{project_id}", response_model=RespuestaProyecto)
def actualizar_proyecto(
    project_id: UUID,
    payload: SolicitudActualizacionProyecto,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> Proyecto:
    return ServicioProyectos(db).actualizar_proyecto(project_id, payload, current_user.id)


@router.delete("/{project_id}", response_model=RespuestaProyecto)
def archivar_proyecto(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> Proyecto:
    return ServicioProyectos(db).archivar_proyecto(project_id, current_user.id)


@router.post("/{project_id}/members", response_model=RespuestaIntegranteProyecto)
def agregar_integrante(
    project_id: UUID,
    payload: SolicitudAgregarIntegrante,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> IntegranteProyecto:
    return ServicioProyectos(db).agregar_integrante(project_id, payload, current_user.id)


@router.get(
    "/{project_id}/member-candidates",
    response_model=list[RespuestaCandidatoIntegranteProyecto],
)
def listar_candidatos_integrantes(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[Usuario]:
    return ServicioProyectos(db).listar_candidatos_integrantes(project_id, current_user.id)


@router.get("/{project_id}/members", response_model=list[RespuestaIntegranteProyecto])
def listar_integrantes(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[RespuestaIntegranteProyecto]:
    members = ServicioProyectos(db).listar_integrantes(project_id, current_user.id)
    users = {
        user.id: user
        for user in db.scalars(
            select(Usuario).where(Usuario.id.in_({member.user_id for member in members}))
        )
    }
    return [
        RespuestaIntegranteProyecto.model_validate(member).model_copy(
            update={
                "full_name": users[member.user_id].full_name,
                "email": users[member.user_id].email,
            }
        )
        for member in members
        if member.user_id in users
    ]


@router.get("/{project_id}/members/me", response_model=RespuestaMiParticipacion)
def obtener_mi_participacion(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> dict:
    return ServicioProyectos(db).mi_participacion(project_id, current_user.id)


@router.patch("/{project_id}/members/{member_id}", response_model=RespuestaIntegranteProyecto)
def actualizar_integrante(
    project_id: UUID,
    member_id: UUID,
    payload: SolicitudActualizarIntegrante,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> IntegranteProyecto:
    return ServicioProyectos(db).actualizar_integrante(project_id, member_id, payload, current_user.id)


@router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def quitar_integrante(
    project_id: UUID,
    member_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> None:
    removed_user_id = ServicioProyectos(db).quitar_integrante(project_id, member_id, current_user.id)
    await manager.disconnect_user(str(project_id), str(removed_user_id))


@router.post("/{project_id}/versions", response_model=RespuestaVersion)
async def crear_version(
    project_id: UUID,
    payload: SolicitudCreacionVersion,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RespuestaVersion:
    version = ServicioProyectos(db).crear_version(
        project_id, payload, current_user.id, idempotency_key
    )
    await manager.broadcast(
        str(project_id),
        {
            "protocol_version": 2,
            "type": "PROJECT_VERSION_CREATED",
            "event_id": str(version.id),
            "project_id": str(project_id),
            "sequence_number": 0,
            "conversation_sequence": 0,
            "correlation_id": str(version.id),
            "occurred_at": version.created_at.isoformat(),
            "persistent": True,
            "actor": {"user_id": str(current_user.id), "display_name": current_user.full_name},
            "payload": {"version_id": str(version.id), "version_number": version.version_number},
        },
    )
    return version


@router.get("/{project_id}/versions", response_model=list[RespuestaVersion])
def listar_versiones(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[dict]:
    return ServicioProyectos(db).listar_versiones(project_id, current_user.id)


@router.get(
    "/{project_id}/versions/{version_id}/restore-preview",
    response_model=RespuestaVistaPreviaRestauracion,
)
async def vista_previa_restauracion(
    project_id: UUID,
    version_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> dict:
    return await ServicioProyectos(db).vista_previa_restauracion(project_id, version_id, current_user.id)


@router.post(
    "/{project_id}/versions/{version_id}/restore",
    response_model=RespuestaRestauracionVersion,
)
async def restaurar_version(
    project_id: UUID,
    version_id: UUID,
    payload: SolicitudRestauracion,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> dict:
    result = await ServicioProyectos(db).restaurar_version(
        project_id,
        version_id,
        current_user.id,
        idempotency_key=idempotency_key,
        payload=payload,
    )
    if result["idempotent_replay"]:
        return result
    await manager.broadcast(
        str(project_id),
        {
            "protocol_version": 2,
            "type": "PROJECT_VERSION_RESTORED",
            "project_id": str(project_id),
            "diagram_id": None,
            "event_id": str(result["event_id"] or result["restore_operation_id"]),
            "sequence_number": result["event_sequence"] or 0,
            "conversation_sequence": 0,
            "correlation_id": str(result["restore_operation_id"]),
            "occurred_at": datetime.now(UTC).isoformat(),
            "persistent": True,
            "actor": {"user_id": str(current_user.id), "display_name": current_user.full_name},
            "payload": {
                "version_id": str(version_id),
                "restore_operation_id": str(result["restore_operation_id"]),
                "project_revision": result["project_revision"],
                "restored_diagram_ids": [str(item) for item in result["restored_diagram_ids"]],
            },
        },
    )
    await manager.broadcast(
        str(project_id),
        {
            "protocol_version": 2,
            "type": "PROJECT_STATE_INVALIDATED",
            "event_id": str(uuid4()),
            "project_id": str(project_id),
            "sequence_number": result["event_sequence"] or 0,
            "conversation_sequence": 0,
            "correlation_id": str(result["restore_operation_id"]),
            "occurred_at": datetime.now(UTC).isoformat(),
            "persistent": False,
            "actor": {"user_id": str(current_user.id), "display_name": current_user.full_name},
            "payload": {
                "project_revision": result["project_revision"],
                "reason": "version_restored",
            },
        },
    )
    return result


@router.get("/{project_id}/activity", response_model=RespuestaPaginaActividad)
def listar_actividad(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    before_sequence: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    type: Annotated[list[str] | None, Query()] = None,
) -> dict:
    return ServicioProyectos(db).listar_actividad(
        project_id,
        current_user.id,
        before_sequence=before_sequence,
        limit=limit,
        event_types=set(type or []),
    )


@router.get("/{project_id}/changes", response_model=list[RespuestaEventoColaboracion])
def listar_cambios(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
    limit: int = 100,
    after_sequence: int | None = None,
) -> list[dict]:
    return ServicioProyectos(db).listar_cambios(project_id, current_user.id, limit, after_sequence)
