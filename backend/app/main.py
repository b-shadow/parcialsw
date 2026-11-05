import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.api.intermediario import NombresContratoMiddleware
from app.core.changelog.ganchos import instalar_ganchos_registro_cambios
from app.core.config.configuracion import settings
from app.core.database.sesion import SessionLocal
from app.core.nosql.cliente import mongo_manager
from app.core.nosql.cliente_sincrono import sync_mongo_manager
from app.core.observability import IntermediarioRegistroSolicitudes
from app.core.redis.cliente import redis_status
from app.core.security.cabeceras import IntermediarioCabecerasSeguridad
from app.core.trabajadores import start_background_workers
from app.modules.acceso_usuarios.routers.autenticacion import router as auth_router
from app.modules.acceso_usuarios.routers.estado import router as acceso_router
from app.modules.acceso_usuarios.routers.usuarios import router as users_router
from app.modules.asistente_proyecto.routers import router as assistant_project_router
from app.modules.generacion_software.routers.ai import router as ai_router
from app.modules.generacion_software.routers.estado import router as generacion_router
from app.modules.generacion_software.routers.generacion import router as generation_router
from app.modules.generacion_software.routers.temas import router as theme_router
from app.modules.modelado_uml.routers.estado import router as uml_router
from app.modules.modelado_uml.routers.uml import router as uml_functional_router
from app.modules.notificaciones.routers import router as notifications_router
from app.modules.proyectos_colaboracion.routers.estado import router as proyectos_router
from app.modules.proyectos_colaboracion.routers.invitaciones import (
    my_router as my_invitations_router,
)
from app.modules.proyectos_colaboracion.routers.invitaciones import (
    router as invitations_router,
)
from app.modules.proyectos_colaboracion.routers.movil import router as mobile_router
from app.modules.proyectos_colaboracion.routers.proyectos import router as projects_router
from app.modules.proyectos_colaboracion.routers.registro_cambios import router as change_log_router
from app.websocket.router import router as websocket_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_manager = mongo_manager
    await mongo_manager.connect(bootstrap=True)
    try:
        async with start_background_workers(app):
            yield
    finally:
        sync_mongo_manager.close()
        await mongo_manager.close()


def crear_aplicacion() -> FastAPI:
    instalar_ganchos_registro_cambios()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend principal modular de la plataforma CASE inteligente.",
        lifespan=lifespan,
    )
    app.state.mongo_manager = mongo_manager

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API error on %s", request.url.path, exc_info=exc)
        response = JSONResponse(
            status_code=500,
            content={"detail": {"code": "INTERNAL_SERVER_ERROR", "message": "Error interno del servidor"}},
        )
        origin = request.headers.get("origin")
        if origin in settings.cors_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    app.add_middleware(IntermediarioRegistroSolicitudes)
    app.add_middleware(IntermediarioCabecerasSeguridad)
    if settings.allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(NombresContratoMiddleware)

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
    async def ready() -> JSONResponse:
        postgres_status = "available"
        current_redis_status = redis_status()
        try:
            with SessionLocal() as session:
                session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            postgres_status = "unavailable"

        mongodb_health = await app.state.mongo_manager.ping()
        mongodb_ready = mongodb_health.available or not mongodb_health.required
        required_migrations = []
        if settings.ai_messages_migration_required:
            from app.core.nosql.commands.migrar_memoria_ia import MIGRATION_NAME as AI_MIGRATION

            required_migrations.append(("ai_memory_migration", AI_MIGRATION))
        if settings.uml_versions_migration_required:
            from app.core.nosql.commands.migrar_versiones_uml import (
                MIGRATION_NAME as UML_VERSION_MIGRATION,
            )

            required_migrations.append(("uml_version_migration", UML_VERSION_MIGRATION))
        if settings.uml_diagrams_migration_required:
            from app.core.nosql.commands.migrar_diagramas_uml import (
                MIGRATION_NAME as UML_DIAGRAM_MIGRATION,
            )

            required_migrations.append(("uml_diagram_migration", UML_DIAGRAM_MIGRATION))
        if settings.phase14_consolidation_required:
            from app.core.nosql.commands.consolidar import (
                MIGRATION_NAME as CONSOLIDATION_MIGRATION,
            )

            required_migrations.append(("phase14_consolidation", CONSOLIDATION_MIGRATION))

        migration_statuses: dict[str, str] = {}
        if required_migrations and mongodb_health.available:
            from pymongo.errors import PyMongoError

            from app.core.nosql.contratos import ColeccionMongo

            for component, migration_name in required_migrations:
                try:
                    checkpoint = await app.state.mongo_manager.database[
                        ColeccionMongo.MIGRATION_CHECKPOINTS.value
                    ].find_one({"migration_name": migration_name}, {"status": 1})
                    migration_statuses[component] = (
                        checkpoint.get("status", "missing") if checkpoint else "missing"
                    )
                except PyMongoError:
                    migration_statuses[component] = "unavailable"
        elif required_migrations:
            migration_statuses = {component: "unavailable" for component, _ in required_migrations}
        reconciliation_status: str | None = None
        if settings.nosql_reconciliation_required and mongodb_health.available:
            from app.core.nosql.contratos import ColeccionMongo

            audit = await app.state.mongo_manager.database[
                ColeccionMongo.OPERATIONAL_AUDITS.value
            ].find_one({}, {"status": 1, "created_at": 1}, sort=[("created_at", -1)])
            if audit is None:
                reconciliation_status = "missing"
            else:
                created_at = audit.get("created_at")
                if created_at is not None and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=UTC)
                age = (
                    (datetime.now(UTC) - created_at).total_seconds()
                    if created_at is not None
                    else settings.nosql_reconciliation_max_age_seconds + 1
                )
                reconciliation_status = (
                    "healthy"
                    if audit.get("status") == "healthy"
                    and age <= settings.nosql_reconciliation_max_age_seconds
                    else "stale_or_degraded"
                )
        elif settings.nosql_reconciliation_required:
            reconciliation_status = "unavailable"
        migration_ready = all(status == "completed" for status in migration_statuses.values())
        reconciliation_ready = reconciliation_status in {None, "healthy"}
        ready_status = (
            postgres_status == "available"
            and mongodb_ready
            and migration_ready
            and reconciliation_ready
        )
        content = {
            "status": "ok" if ready_status else "degraded",
            "database": postgres_status,
            "redis": current_redis_status,
            "components": {
                "postgresql": {"status": postgres_status, "required": True},
                "mongodb": {
                    "status": mongodb_health.status,
                    "required": mongodb_health.required,
                    "database": mongodb_health.database,
                },
                "redis": {
                    "status": current_redis_status,
                    "required": False,
                },
            },
        }
        for component, migration_status in migration_statuses.items():
            content["components"][component] = {
                "status": migration_status,
                "required": True,
            }
        if reconciliation_status is not None:
            content["components"]["nosql_reconciliation"] = {
                "status": reconciliation_status,
                "required": True,
            }
        return JSONResponse(
            status_code=200 if ready_status else 503,
            content=content,
        )

    return app


app = crear_aplicacion()
