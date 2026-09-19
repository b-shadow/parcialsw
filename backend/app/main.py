from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.core.observability import RequestLoggingMiddleware
from app.core.security.headers import SecurityHeadersMiddleware
from app.modules.acceso_usuarios.routers.auth import router as auth_router
from app.modules.acceso_usuarios.routers.health import router as acceso_router
from app.modules.acceso_usuarios.routers.users import router as users_router
from app.modules.generacion_software.routers.ai import router as ai_router
from app.modules.generacion_software.routers.generation import router as generation_router
from app.modules.generacion_software.routers.health import router as generacion_router
from app.modules.modelado_uml.routers.health import router as uml_router
from app.modules.modelado_uml.routers.uml import router as uml_functional_router
from app.modules.proyectos_colaboracion.routers.health import router as proyectos_router
from app.modules.proyectos_colaboracion.routers.projects import router as projects_router
from app.websocket.router import router as websocket_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend principal modular de la plataforma CASE inteligente.",
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
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(users_router, prefix=settings.api_prefix)
    app.include_router(proyectos_router, prefix=settings.api_prefix)
    app.include_router(projects_router, prefix=settings.api_prefix)
    app.include_router(uml_router, prefix=settings.api_prefix)
    app.include_router(uml_functional_router, prefix=settings.api_prefix)
    app.include_router(generacion_router, prefix=settings.api_prefix)
    app.include_router(ai_router, prefix=settings.api_prefix)
    app.include_router(generation_router, prefix=settings.api_prefix)
    app.include_router(websocket_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok", "component": "backend"}

    @app.get("/ready", tags=["health"])
    def ready() -> dict[str, str]:
        try:
            with SessionLocal() as session:
                session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return {"status": "degraded", "database": "unavailable"}
        return {"status": "ok", "database": "available"}

    return app


app = create_app()
