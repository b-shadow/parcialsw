import asyncio
import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient
from pymongo.errors import WriteError

from app.core.nosql.contratos import ColeccionMongo, DocumentoDiagramaUML
from app.core.nosql.esquema import asegurar_esquema_mongo
from app.core.nosql.repositorios import RepositorioDiagramasUML

MONGODB_TEST_URI = os.getenv("MONGODB_TEST_URI")
pytestmark = pytest.mark.skipif(not MONGODB_TEST_URI, reason="MONGODB_TEST_URI is not configured")


def test_phase10_real_mongodb_contracts_indexes_and_repository() -> None:
    async def scenario() -> None:
        database_name = f"case_phase10_test_{uuid4().hex}"
        client = AsyncMongoClient(
            MONGODB_TEST_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            tz_aware=True,
        )
        database = client[database_name]
        try:
            await client.admin.command("ping")
            await asegurar_esquema_mongo(database)
            await asegurar_esquema_mongo(database)

            now = datetime.now(UTC)
            document = DocumentoDiagramaUML(
                _id=uuid4(),
                project_id=uuid4(),
                revision=1,
                content={"classes": [], "relationships": []},
                content_hash="c" * 64,
                created_at=now,
                updated_at=now,
            )
            repository = RepositorioDiagramasUML(database)
            stored = await repository.upsert(document)
            loaded = await repository.get(document.id)

            assert stored.id == document.id
            assert loaded is not None and loaded.project_id == document.project_id
            assert await repository.count() == 1

            indexes = await database[ColeccionMongo.UML_DIAGRAMS.value].index_information()
            assert "uq_diagramas_uml_proyecto" in indexes

            with pytest.raises(WriteError):
                await database[ColeccionMongo.UML_DIAGRAMS.value].insert_one(
                    {"_id": str(uuid4()), "schema_version": 1}
                )
        finally:
            await client.drop_database(database_name)
            await client.close()

    asyncio.run(scenario())
