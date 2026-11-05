"""Migración física de documentos MongoDB existentes a nombres en español."""

import asyncio
import os
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient

from app.core.nosql.contratos import (
    ColeccionMongo,
    DocumentoAuditoriaOperativa,
    DocumentoDiagramaUML,
    DocumentoInstantaneaContextoIA,
    DocumentoMensajeIA,
    DocumentoPuntoControlMigracion,
    DocumentoVersionDiagramaUML,
    MutacionMongo,
)
from app.core.nosql.esquema import asegurar_esquema_mongo
from app.core.nosql.nombres_mongo import COLECCIONES
from app.core.nosql.repositorios import RepositorioDiagramasUML, RepositorioMensajesIA

pytestmark = pytest.mark.skipif(
    not os.getenv("MONGODB_TEST_URI"), reason="Se requiere MongoDB de pruebas"
)


def test_eventos_sql_pendientes_aceptan_nombre_anterior_de_coleccion() -> None:
    mutation = MutacionMongo.model_validate({
        "collection": "uml_diagrams", "operation": "delete",
        "document_id": str(uuid4()),
    })
    assert mutation.collection == ColeccionMongo.UML_DIAGRAMS


def test_colecciones_y_documentos_historicos_se_migran_sin_perder_contenido() -> None:
    async def scenario() -> None:
        client = AsyncMongoClient(os.environ["MONGODB_TEST_URI"], tz_aware=True)
        nombre = f"case_nombres_mongo_test_{uuid4().hex}"
        database = client[nombre]
        proyecto_id, diagrama_id, conversacion_id = uuid4(), uuid4(), uuid4()
        try:
            diagram = DocumentoDiagramaUML(
                _id=diagrama_id, project_id=proyecto_id, revision=2,
                content={
                    "id": str(diagrama_id), "project_id": str(proyecto_id),
                    "name": "Academico", "classes": [{"id": str(uuid4()), "name": "Alumno"}],
                    "relationships": [],
                },
                content_hash="a" * 64,
            )
            message = DocumentoMensajeIA(
                _id=uuid4(), project_id=proyecto_id, conversation_id=conversacion_id,
                author_user_id=uuid4(), role="user", sequence_number=1,
                content="Explica el modelo", correlation_id=uuid4(), content_hash="b" * 64,
            )
            await database["uml_diagrams"].insert_one(diagram.to_mongo())
            segundo = DocumentoDiagramaUML(
                _id=uuid4(), project_id=uuid4(), revision=1,
                content={"classes": [], "relationships": []}, content_hash="e" * 64,
            )
            await database["uml_diagrams"].insert_one(segundo.to_mongo())
            await database["ai_messages"].insert_one(message.to_mongo())
            await database["uml_diagrams"].create_index(
                "project_id", name="uq_uml_diagrams_project", unique=True
            )
            await database["uml_diagrams"].create_index("revision", name="ix_personalizado")
            version = DocumentoVersionDiagramaUML(
                _id=uuid4(), project_id=proyecto_id, diagram_id=diagrama_id,
                version_number=1, content=diagram.content, content_hash="c" * 64,
            )
            context = DocumentoInstantaneaContextoIA(
                _id=uuid4(), project_id=proyecto_id, conversation_id=conversacion_id,
                until_sequence=1, summary="Primer mensaje", content_hash="d" * 64,
            )
            checkpoint = DocumentoPuntoControlMigracion(
                _id=uuid4(), migration_name="prueba", status="completed",
            )
            audit = DocumentoAuditoriaOperativa(
                _id=uuid4(), status="healthy", duration_ms=1,
            )
            antiguos = {
                "uml_diagram_versions": version.to_mongo(),
                "ai_context_snapshots": context.to_mongo(),
                "migration_checkpoints": checkpoint.to_mongo(),
                "nosql_operational_audits": audit.to_mongo(),
                "nosql_processed_events": {
                    "_id": str(uuid4()), "schema_version": 1,
                    "created_at": diagram.created_at, "updated_at": diagram.updated_at,
                    "idempotency_key": "prueba-evento", "event_id": str(uuid4()),
                    "collection": "uml_diagrams", "operation": "upsert",
                    "processed_at": diagram.updated_at,
                },
            }
            for coleccion, documento in antiguos.items():
                await database[coleccion].insert_one(documento)

            await asegurar_esquema_mongo(database)
            await asegurar_esquema_mongo(database)

            nombres = set(await database.list_collection_names())
            assert set(COLECCIONES).isdisjoint(nombres)
            assert set(COLECCIONES.values()) <= nombres
            raw_diagram = await database[ColeccionMongo.UML_DIAGRAMS.value].find_one(
                {"_id": str(diagrama_id)}
            )
            assert raw_diagram["proyecto_id"] == str(proyecto_id)
            assert raw_diagram["contenido"]["clases"][0]["nombre"] == "Alumno"
            assert "project_id" not in raw_diagram and "content" not in raw_diagram
            assert raw_diagram["hash_contenido"] == "a" * 64
            assert await database[ColeccionMongo.UML_DIAGRAMS.value].count_documents({}) == 2
            indices = await database[ColeccionMongo.UML_DIAGRAMS.value].index_information()
            assert "uq_uml_diagrams_project" not in indices
            assert "uq_diagramas_uml_proyecto" in indices
            assert "ix_personalizado" in indices
            raw_message = await database[ColeccionMongo.AI_MESSAGES.value].find_one(
                {"_id": str(message.id)}
            )
            assert raw_message["contenido"] == "Explica el modelo"
            assert raw_message["conversacion_id"] == str(conversacion_id)
            for antiguo, documento in antiguos.items():
                guardado = await database[COLECCIONES[antiguo]].find_one({"_id": documento["_id"]})
                assert guardado is not None
                assert "schema_version" not in guardado
                assert guardado["version_esquema"] == 1
            recibo = await database[ColeccionMongo.PROCESSED_EVENTS.value].find_one(
                {"clave_idempotencia": "prueba-evento"}
            )
            assert recibo["coleccion"] == ColeccionMongo.UML_DIAGRAMS.value

            recovered = await RepositorioDiagramasUML(database).get(diagrama_id)
            recovered_message = await RepositorioMensajesIA(database).get(message.id)
            assert recovered.content == diagram.content
            assert recovered_message.content == message.content
        finally:
            await client.drop_database(nombre)
            await client.close()

    asyncio.run(scenario())
