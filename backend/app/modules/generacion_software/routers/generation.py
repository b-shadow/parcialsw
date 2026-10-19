from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.generacion_software.models import (
    CoordinatedGeneration,
    GeneratedBackend,
    GeneratedFrontend,
    UmlTransformation,
)
from app.modules.generacion_software.schemas.generation import (
    BackendGenerationRequest,
    CoordinatedGenerationRequest,
    CoordinatedGenerationResponse,
    CoordinatedPreflightRequest,
    FrontendGenerationRequest,
    GeneratedBackendResponse,
    GeneratedFrontendResponse,
    GenerationPlanResponse,
    TransformationRequest,
    TransformationResponse,
)
from app.modules.generacion_software.services.generation_service import GenerationService
from app.modules.notificaciones.schemas.notification import NotificationDeepLink
from app.modules.notificaciones.services import DomainNotificationEvent, NotificationService
from app.modules.proyectos_colaboracion.models import CollaborationEvent
from app.modules.proyectos_colaboracion.repositories.project_repository import ProjectRepository

router = APIRouter(prefix="/generation", tags=["generacion-software"])


def _record_completed(db: Session, generated, user: User, label: str) -> None:
    projects = ProjectRepository(db)
    projects.get_for_update(generated.project_id)
    event = CollaborationEvent(
        project_id=generated.project_id, diagram_id=None, user_id=user.id,
        client_event_id=uuid4(), sequence_number=projects.next_event_sequence(generated.project_id),
        event_type="GENERATION_COMPLETED", element_type="generation", element_id=generated.id,
        base_version=None,
        payload={"generation_id": str(generated.id), "kind": label, "status": generated.status},
        resource_type="generation", resource_id=generated.id,
        correlation_id=generated.id, summary_key="activity.generation_completed",
    )
    db.add(event)
    NotificationService(db).record(DomainNotificationEvent(
        type="GENERATION_COMPLETED", category="generation",
        title=f"{label} generado", body=f"{generated.name} esta listo para descargar.",
        recipient_user_ids={user.id}, dedup_entity_id=generated.id,
        project_id=generated.project_id, actor_user_id=user.id,
        resource_type="generation", resource_id=generated.id,
        deep_link=NotificationDeepLink(route_name="generation"), exclude_actor=False,
    ))
    db.commit()


@router.get("/transformations/{transformation_id}/ui-manifest")
def get_ui_manifest(
    transformation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return GenerationService(db).get_ui_manifest(transformation_id, current_user.id)


@router.post("/coordinated/preflight", response_model=GenerationPlanResponse)
def preflight_coordinated(
    payload: CoordinatedPreflightRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return GenerationService(db).preflight_coordinated(payload, current_user.id)


@router.post(
    "/coordinated",
    response_model=CoordinatedGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_coordinated(
    payload: CoordinatedGenerationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CoordinatedGeneration:
    generated = GenerationService(db).generate_coordinated(payload, current_user.id)
    _record_completed(db, generated, current_user, "Proyecto full stack")
    return generated


@router.get("/coordinated/{generation_id}", response_model=CoordinatedGenerationResponse)
def get_coordinated(
    generation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CoordinatedGeneration:
    return GenerationService(db).get_coordinated(generation_id, current_user.id)


@router.get("/coordinated/{generation_id}/download")
def download_coordinated(
    generation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    artifact_path = GenerationService(db).get_coordinated_artifact_path(
        generation_id, current_user.id
    )
    return FileResponse(
        artifact_path,
        media_type="application/zip",
        filename=artifact_path.rsplit("\\", maxsplit=1)[-1].rsplit("/", maxsplit=1)[-1],
    )


@router.post("/transformations", response_model=TransformationResponse, status_code=status.HTTP_201_CREATED)
def transform(
    payload: TransformationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UmlTransformation:
    return GenerationService(db).transform(payload, current_user.id)


@router.post("/spring-boot", response_model=GeneratedBackendResponse, status_code=status.HTTP_201_CREATED)
def generate_backend(
    payload: BackendGenerationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GeneratedBackend:
    generated = GenerationService(db).generate_backend(payload, current_user.id)
    _record_completed(db, generated, current_user, "Backend Spring Boot")
    return generated


@router.get(
    "/projects/{project_id}/spring-boot",
    response_model=list[GeneratedBackendResponse],
)
def list_backends(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[GeneratedBackend]:
    return GenerationService(db).list_backends(project_id, current_user.id)


@router.get("/spring-boot/{backend_id}/download")
def download_backend(
    backend_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    artifact_path = GenerationService(db).get_backend_artifact_path(backend_id, current_user.id)
    return FileResponse(
        artifact_path,
        media_type="application/zip",
        filename=artifact_path.rsplit("\\", maxsplit=1)[-1].rsplit("/", maxsplit=1)[-1],
    )


@router.post("/flutter", response_model=GeneratedFrontendResponse, status_code=status.HTTP_201_CREATED)
def generate_frontend(
    payload: FrontendGenerationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GeneratedFrontend:
    generated = GenerationService(db).generate_frontend(payload, current_user.id)
    _record_completed(db, generated, current_user, "Frontend Flutter")
    return generated


@router.get(
    "/projects/{project_id}/flutter",
    response_model=list[GeneratedFrontendResponse],
)
def list_frontends(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[GeneratedFrontend]:
    return GenerationService(db).list_frontends(project_id, current_user.id)


@router.get("/flutter/{frontend_id}/download")
def download_frontend(
    frontend_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    artifact_path = GenerationService(db).get_frontend_artifact_path(frontend_id, current_user.id)
    return FileResponse(
        artifact_path,
        media_type="application/zip",
        filename=artifact_path.rsplit("\\", maxsplit=1)[-1].rsplit("/", maxsplit=1)[-1],
    )
