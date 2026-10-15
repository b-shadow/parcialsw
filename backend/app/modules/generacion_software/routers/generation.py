from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database.session import get_db
from app.core.security.dependencies import get_current_user
from app.modules.acceso_usuarios.models import User
from app.modules.generacion_software.models import (
    GeneratedBackend,
    GeneratedFrontend,
    UmlTransformation,
)
from app.modules.generacion_software.schemas.generation import (
    BackendGenerationRequest,
    FrontendGenerationRequest,
    GeneratedBackendResponse,
    GeneratedFrontendResponse,
    TransformationRequest,
    TransformationResponse,
)
from app.modules.generacion_software.services.generation_service import GenerationService
from app.modules.notificaciones.services import send_user_push

router = APIRouter(prefix="/generation", tags=["generacion-software"])


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
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GeneratedBackend:
    generated = GenerationService(db).generate_backend(payload, current_user.id)
    background_tasks.add_task(
        send_user_push,
        current_user.id,
        {
            "title": "Backend generado",
            "body": f"El proyecto Spring Boot {generated.name} esta listo para descargar.",
            "url": "/generacion",
            "tag": f"generation-backend-{generated.id}",
        },
    )
    return generated


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
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GeneratedFrontend:
    generated = GenerationService(db).generate_frontend(payload, current_user.id)
    background_tasks.add_task(
        send_user_push,
        current_user.id,
        {
            "title": "Frontend generado",
            "body": f"La aplicacion Flutter {generated.name} esta lista para descargar.",
            "url": "/generacion",
            "tag": f"generation-frontend-{generated.id}",
        },
    )
    return generated


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
