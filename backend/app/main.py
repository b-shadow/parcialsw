from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.changelog.hooks import install_change_log_hooks
from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.core.observability import RequestLoggingMiddleware
from app.core.redis.client import redis_status
from app.core.security.headers import SecurityHeadersMiddleware
from app.core.workers import start_background_workers
from app.modules.acceso_usuarios.routers.auth import router as auth_router
from app.modules.acceso_usuarios.routers.health import router as acceso_router
from app.modules.acceso_usuarios.routers.users import router as users_router
from app.modules.asistente_proyecto.routers import router as assistant_project_router
from app.modules.generacion_software.routers.ai import router as ai_router
from app.modules.generacion_software.routers.generation import router as generation_router
from app.modules.generacion_software.routers.health import router as generacion_router
from app.modules.generacion_software.routers.theme import router as theme_router
from app.modules.modelado_uml.routers.health import router as uml_router
from app.modules.modelado_uml.routers.uml import router as uml_functional_router
from app.modules.notificaciones.routers import router as notifications_router
from app.modules.proyectos_colaboracion.routers.change_log import router as change_log_router
from app.modules.proyectos_colaboracion.routers.health import router as proyectos_router
from app.modules.proyectos_colaboracion.routers.invitations import (
    my_router as my_invitations_router,
    router as invitations_router,
)
from app.modules.proyectos_colaboracion.routers.mobile import router as mobile_router
from app.modules.proyectos_colaboracion.routers.projects import router as projects_router
from app.websocket.router import router as websocket_router


def create_app() -> FastAPI:
    install_change_log_hooks()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend principal modular de la plataforma CASE inteligente.",
        lifespan=start_background_workers,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    if settings.allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(acceso_router, prefix=settings.api_prefix)
    app.include_router(assistant_project_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(users_router, prefix=settings.api_prefix)
    app.include_router(proyectos_router, prefix=settings.api_prefix)
    app.include_router(projects_router, prefix=settings.api_prefix)
    app.include_router(change_log_router, prefix=settings.api_prefix)
    app.include_router(invitations_router, prefix=settings.api_prefix)
    app.include_router(my_invitations_router, prefix=settings.api_prefix)
    app.include_router(mobile_router, prefix=settings.api_prefix)
    app.include_router(uml_router, prefix=settings.api_prefix)
    app.include_router(uml_functional_router, prefix=settings.api_prefix)
    app.include_router(generacion_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)
    app.include_router(generation_router, prefix=settings.api_prefix)
    app.include_router(theme_router, prefix=settings.api_prefix)
    app.include_router(notifications_router, prefix=settings.api_prefix)
    app.include_router(websocket_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok", "component": "backend"}

    @app.get("/ready", tags=["health"])
    def ready() -> JSONResponse:
        current_redis_status = redis_status()
        try:
            with SessionLocal() as session:
                session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "degraded",
                    "database": "unavailable",
                },
            )
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "database": "available",
                "redis": current_redis_status,
            },
        )

    return app


app = create_app()
