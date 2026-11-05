from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database.sesion import obtener_sesion_bd
from app.core.security.dependencias import obtener_usuario_actual
from app.modules.acceso_usuarios.models import Usuario
from app.modules.generacion_software.models import (
    BackendGenerado,
    FrontendGenerado,
    GeneracionCoordinada,
    TransformacionUML,
)
from app.modules.generacion_software.schemas.generacion import (
    RespuestaBackendGenerado,
    RespuestaFrontendGenerado,
    RespuestaGeneracionCoordinada,
    RespuestaPlanGeneracion,
    RespuestaTransformacion,
    SolicitudGeneracionBackend,
    SolicitudGeneracionCoordinada,
    SolicitudGeneracionFrontend,
    SolicitudTransformacion,
    SolicitudVerificacionPreviaCoordinada,
)
from app.modules.generacion_software.services.servicio_generacion import ServicioGeneracion
from app.modules.notificaciones.schemas.notificacion import EnlaceProfundoNotificacion
from app.modules.notificaciones.services import EventoNotificacionDominio, ServicioNotificaciones
from app.modules.proyectos_colaboracion.models import EventoColaboracion
from app.modules.proyectos_colaboracion.repositories.repositorio_proyectos import (
    RepositorioProyectos,
)

router = APIRouter(prefix="/generation", tags=["generacion-software"])


def _registrar_finalizada(db: Session, generated, user: Usuario, label: str) -> None:
    projects = RepositorioProyectos(db)
    projects.obtener_para_actualizar(generated.project_id)
    event = EventoColaboracion(
        project_id=generated.project_id, diagram_id=None, user_id=user.id,
        client_event_id=uuid4(), sequence_number=projects.siguiente_secuencia_evento(generated.project_id),
        event_type="GENERATION_COMPLETED", element_type="generation", element_id=generated.id,
        base_version=None,
        payload={"generation_id": str(generated.id), "kind": label, "status": generated.status},
        resource_type="generation", resource_id=generated.id,
        correlation_id=generated.id, summary_key="activity.generation_completed",
    )
    db.add(event)
    ServicioNotificaciones(db).record(EventoNotificacionDominio(
        type="GENERATION_COMPLETED", category="generation",
        title=f"{label} generado", body=f"{generated.name} esta listo para descargar.",
        recipient_user_ids={user.id}, dedup_entity_id=generated.id,
        project_id=generated.project_id, actor_user_id=user.id,
        resource_type="generation", resource_id=generated.id,
        deep_link=EnlaceProfundoNotificacion(route_name="generation"), exclude_actor=False,
    ))
    db.commit()


@router.get("/transformations/{transformation_id}/ui-manifest")
def obtener_manifiesto_ui(
    transformation_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> dict:
    return ServicioGeneracion(db).obtener_manifiesto_ui(transformation_id, current_user.id)


@router.post("/coordinated/preflight", response_model=RespuestaPlanGeneracion)
def verificar_coordinada(
    payload: SolicitudVerificacionPreviaCoordinada,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> dict:
    return ServicioGeneracion(db).verificar_coordinada(payload, current_user.id)


@router.post(
    "/coordinated",
    response_model=RespuestaGeneracionCoordinada,
    status_code=status.HTTP_201_CREATED,
)
def generar_coordinada(
    payload: SolicitudGeneracionCoordinada,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> GeneracionCoordinada:
    generated = ServicioGeneracion(db).generar_coordinada(payload, current_user.id)
    _registrar_finalizada(db, generated, current_user, "Proyecto full stack")
    return generated


@router.get("/coordinated/{generation_id}", response_model=RespuestaGeneracionCoordinada)
def obtener_coordinada(
    generation_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> GeneracionCoordinada:
    return ServicioGeneracion(db).obtener_coordinada(generation_id, current_user.id)


@router.get("/coordinated/{generation_id}/download")
def descargar_coordinada(
    generation_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> FileResponse:
    artifact_path = ServicioGeneracion(db).obtener_ruta_artefacto_coordinado(
        generation_id, current_user.id
    )
    return FileResponse(
        artifact_path,
        media_type="application/zip",
        filename=artifact_path.rsplit("\\", maxsplit=1)[-1].rsplit("/", maxsplit=1)[-1],
    )


@router.post("/transformations", response_model=RespuestaTransformacion, status_code=status.HTTP_201_CREATED)
def transform(
    payload: SolicitudTransformacion,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> TransformacionUML:
    return ServicioGeneracion(db).transform(payload, current_user.id)


@router.post("/spring-boot", response_model=RespuestaBackendGenerado, status_code=status.HTTP_201_CREATED)
def generar_backend(
    payload: SolicitudGeneracionBackend,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> BackendGenerado:
    generated = ServicioGeneracion(db).generar_backend(payload, current_user.id)
    _registrar_finalizada(db, generated, current_user, "Backend Spring Boot")
    return generated


@router.get(
    "/projects/{project_id}/spring-boot",
    response_model=list[RespuestaBackendGenerado],
)
def listar_backends(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[BackendGenerado]:
    return ServicioGeneracion(db).listar_backends(project_id, current_user.id)


@router.get("/spring-boot/{backend_id}/download")
def descargar_backend(
    backend_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> FileResponse:
    artifact_path = ServicioGeneracion(db).obtener_ruta_artefacto_backend(backend_id, current_user.id)
    return FileResponse(
        artifact_path,
        media_type="application/zip",
        filename=artifact_path.rsplit("\\", maxsplit=1)[-1].rsplit("/", maxsplit=1)[-1],
    )


@router.post("/flutter", response_model=RespuestaFrontendGenerado, status_code=status.HTTP_201_CREATED)
def generar_frontend(
    payload: SolicitudGeneracionFrontend,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> FrontendGenerado:
    generated = ServicioGeneracion(db).generar_frontend(payload, current_user.id)
    _registrar_finalizada(db, generated, current_user, "Frontend Flutter")
    return generated


@router.get(
    "/projects/{project_id}/flutter",
    response_model=list[RespuestaFrontendGenerado],
)
def listar_frontends(
    project_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> list[FrontendGenerado]:
    return ServicioGeneracion(db).listar_frontends(project_id, current_user.id)


@router.get("/flutter/{frontend_id}/download")
def descargar_frontend(
    frontend_id: UUID,
    current_user: Annotated[Usuario, Depends(obtener_usuario_actual)],
    db: Annotated[Session, Depends(obtener_sesion_bd)],
) -> FileResponse:
    artifact_path = ServicioGeneracion(db).obtener_ruta_artefacto_frontend(frontend_id, current_user.id)
    return FileResponse(
        artifact_path,
        media_type="application/zip",
        filename=artifact_path.rsplit("\\", maxsplit=1)[-1].rsplit("/", maxsplit=1)[-1],
    )
