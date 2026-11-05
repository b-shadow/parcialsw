"""End-to-end assistant persistence with isolated PostgreSQL and MongoDB databases."""

import asyncio
import os
from uuid import UUID, uuid4

import pytest

from app.core.config.configuracion import settings
from app.core.database.sesion import SessionLocal
from app.core.nosql.cliente import mongo_manager
from app.core.nosql.cliente_sincrono import sync_mongo_manager
from app.modules.acceso_usuarios.models import Usuario
from app.modules.asistente_proyecto.schemas.esquemas_asistente import (
    ActualizacionConfiguracionIAProyecto,
    CreacionConversacionIA,
    SolicitudInteraccionIA,
)
from app.modules.asistente_proyecto.services.constructor_contexto import ConstructorContextoProyecto
from app.modules.asistente_proyecto.services.servicio_aplicacion_ia_proyecto import (
    ServicioAplicacionIAProyecto,
)
from app.modules.asistente_proyecto.services.servicio_asistente import ServicioContratoAsistente
from app.modules.asistente_proyecto.services.servicio_ejecucion_acciones import (
    ServicioEjecucionAccionesIA,
)
from app.modules.asistente_proyecto.services.servicio_memoria_conversacion import (
    ServicioMemoriaConversacion,
)
from app.modules.modelado_uml.schemas.uml import SolicitudCreacionClaseUML
from app.modules.modelado_uml.services.servicio_uml import ServicioUML
from app.modules.proyectos_colaboracion.schemas.proyecto import SolicitudCreacionProyecto
from app.modules.proyectos_colaboracion.services.servicio_proyectos import ServicioProyectos

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("MONGODB_TEST_URI"),
    reason="isolated DATABASE_URL and MONGODB_TEST_URI are required",
)


def test_assistant_explains_diagram_and_persists_messages_in_mongodb() -> None:
    assert "test" in settings.database_url.rsplit("/", 1)[-1]
    assert "test" in settings.mongodb_database

    async def scenario() -> None:
        health = await mongo_manager.connect(bootstrap=True)
        assert health.available
        try:
            with SessionLocal() as db:
                user = Usuario(
                    full_name="Asistente de prueba",
                    email=f"assistant-{uuid4()}@example.com",
                    password_hash="unused",
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                project = ServicioProyectos(db).crear_proyecto(
                    SolicitudCreacionProyecto(name="Inscripciones de prueba"), user.id
                )
                diagram = ServicioUML(db).listar_diagramas(project.id, user.id)[0]
                ServicioUML(db).crear_clase(
                    diagram.id, SolicitudCreacionClaseUML(name="Estudiante"), user.id
                )
                contracts = ServicioContratoAsistente(db)
                contracts.actualizar_configuracion(
                    project.id, user.id,
                    ActualizacionConfiguracionIAProyecto(preferred_provider="rule_engine"),
                )
                conversation = contracts.crear_conversacion(
                    project.id, user.id, CreacionConversacionIA()
                )

                application = ServicioAplicacionIAProyecto(db)
                first_client_id = uuid4()
                first_request = SolicitudInteraccionIA(
                    client_message_id=first_client_id,
                    conversation_id=conversation.id,
                    diagram_id=diagram.id,
                    content="¿Qué opinas de este diagrama?",
                )
                response = await application.interactuar(
                    project.id,
                    user.id,
                    first_request,
                )
                assert response.status == "completed"
                assert response.answer
                assert response.detected_intents
                page = await contracts.listar_mensajes(
                    project.id, user.id, None, None, 20, conversation.id
                )
                assert [item.role for item in page.items] == ["user", "assistant"]
                assert all(item.status == "completed" for item in page.items)
                assert page.items[-1].detected_intents == response.detected_intents
                assert page.items[-1].content == response.answer

                repeated = await application.interactuar(project.id, user.id, first_request)
                assert repeated.message_id == response.message_id
                assert repeated.conversation_sequence == response.conversation_sequence

                review = await application.interactuar(
                    project.id,
                    user.id,
                    SolicitudInteraccionIA(
                        client_message_id=uuid4(),
                        conversation_id=conversation.id,
                        diagram_id=diagram.id,
                        content="¿Qué mejoras recomiendas para este diagrama?",
                    ),
                )
                assert review.recommendations

                change = await application.interactuar(
                    project.id,
                    user.id,
                    SolicitudInteraccionIA(
                        client_message_id=uuid4(),
                        conversation_id=conversation.id,
                        diagram_id=diagram.id,
                        content="Crea una clase Producto",
                    ),
                )
                assert change.actions
                assert change.actions[0]["status"] == "proposed"
                action, idempotent = ServicioEjecucionAccionesIA(db).confirmar(
                    project.id, UUID(change.actions[0]["id"]), user.id
                )
                assert action.status == "applied"
                assert not idempotent
                assert {item.name for item in ServicioUML(db).listar_clases(diagram.id, user.id)} == {
                    "Estudiante", "Producto"
                }

                summary = await ServicioMemoriaConversacion(db).resumir_si_es_necesario(
                    project.id, user.id, conversation.id, force=True
                )
                assert summary is not None
                snapshot = await contracts.documents.obtener_contexto_reciente_seguro(conversation.id)
                assert snapshot is not None
                assert snapshot.until_sequence == 6

                another_chat = contracts.crear_conversacion(
                    project.id, user.id, CreacionConversacionIA()
                )
                memory = await ConstructorContextoProyecto(db)._memoria_conversaciones_proyecto(
                    project.id, another_chat
                )
                assert memory is not None
                assert "chat anterior" in memory
                assert "Producto" in memory

                correction = await application.interactuar(
                    project.id,
                    user.id,
                    SolicitudInteraccionIA(
                        client_message_id=uuid4(),
                        conversation_id=conversation.id,
                        diagram_id=diagram.id,
                        content="Corrige el diagrama aplicando esta recomendación: Identificadores ausentes.",
                    ),
                )
                assert correction.actions
                assert all(item["action_type"] == "create_attribute" for item in correction.actions)
                for planned in correction.actions:
                    applied, duplicate = ServicioEjecucionAccionesIA(db).confirmar(
                        project.id, UUID(planned["id"]), user.id
                    )
                    assert applied.status == "applied"
                    assert not duplicate
                classes = ServicioUML(db).obtener_modelo_diagrama(diagram.id, user.id).classes
                assert all(any(attribute.name == "id" for attribute in item.attributes) for item in classes)
        finally:
            sync_mongo_manager.close()
            await mongo_manager.close()

    asyncio.run(scenario())
