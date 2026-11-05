"""Persistencia actual de chats entre PostgreSQL y MongoDB."""

import asyncio
import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.core.config.configuracion import settings
from app.core.database.sesion import SessionLocal
from app.core.nosql.cliente import mongo_manager
from app.core.nosql.cliente_sincrono import sync_mongo_manager
from app.core.nosql.contratos import ColeccionMongo
from app.modules.acceso_usuarios.models import Usuario
from app.modules.asistente_proyecto.schemas import CreacionInternaMensajeIA
from app.modules.asistente_proyecto.schemas.esquemas_asistente import CreacionConversacionIA
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente
from app.modules.proyectos_colaboracion.schemas.proyecto import SolicitudCreacionProyecto
from app.modules.proyectos_colaboracion.services.servicio_proyectos import ServicioProyectos

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("MONGODB_TEST_URI"),
    reason="Se requieren PostgreSQL y MongoDB aislados",
)


def test_mensaje_actual_conserva_relacion_sql_y_idempotencia_mongo() -> None:
    assert settings.database_url.rsplit("/", 1)[-1].endswith("test")
    assert settings.mongodb_database.endswith("test")

    async def scenario() -> None:
        assert (await mongo_manager.connect(bootstrap=True)).available
        try:
            with SessionLocal() as db:
                user = Usuario(
                    full_name="Prueba de memoria",
                    email=f"memoria-{uuid4()}@example.com",
                    password_hash="unused",
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                project = ServicioProyectos(db).crear_proyecto(
                    SolicitudCreacionProyecto(name="Memoria de prueba"), user.id
                )
                service = ServicioContratoAsistente(db)
                conversation = service.crear_conversacion(
                    project.id, user.id, CreacionConversacionIA()
                )
                client_id = uuid4()
                first, created = service.crear_mensaje(
                    project.id,
                    user.id,
                    CreacionInternaMensajeIA(
                        role="user",
                        content="Revisa el modelo",
                        client_message_id=client_id,
                        correlation_id=uuid4(),
                    ),
                    conversation.id,
                )
                repeated, repeated_created = service.crear_mensaje(
                    project.id,
                    user.id,
                    CreacionInternaMensajeIA(
                        role="user",
                        content="Revisa el modelo",
                        client_message_id=client_id,
                        correlation_id=uuid4(),
                    ),
                    conversation.id,
                )
                assert created and not repeated_created
                assert repeated.id == first.id
                assert db.scalar(text("SELECT count(*) FROM conversaciones_ia WHERE proyecto_id = :id"),
                                 {"id": project.id}) == 1
                page = await service.listar_mensajes(
                    project.id, user.id, None, None, 20, conversation.id
                )
                assert [item.content for item in page.items] == ["Revisa el modelo"]
                stored = sync_mongo_manager.database[ColeccionMongo.AI_MESSAGES.value].find_one(
                    {"_id": str(first.id)}
                )
                assert stored["project_id"] == str(project.id)
                assert stored["conversation_id"] == str(conversation.id)
                assert stored["sequence_number"] == 1
        finally:
            sync_mongo_manager.close()
            await mongo_manager.close()

    asyncio.run(scenario())
