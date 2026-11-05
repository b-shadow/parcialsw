import asyncio
import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient
from sqlalchemy import delete

from app.core.database.sesion import SessionLocal
from app.core.nosql.commands.migrar_versiones_uml import (
    MIGRATION_NAME,
    MigradorVersionesUML,
)
from app.core.nosql.contratos import ColeccionMongo
from app.core.nosql.esquema import asegurar_esquema_mongo
from app.core.nosql.nombres_mongo import traducir_documento
from app.modules.acceso_usuarios.models import Usuario
from app.modules.modelado_uml.models import DiagramaUML
from app.modules.proyectos_colaboracion.models import IntegranteProyecto, Proyecto, VersionProyecto
from app.modules.proyectos_colaboracion.schemas.instantanea import (
    InstantaneaProyecto,
    InstantaneaProyectoV2,
    hash_instantanea_sha256,
    normalizar_instantanea_proyecto,
)

MONGODB_TEST_URI = os.getenv("MONGODB_TEST_URI")
DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not MONGODB_TEST_URI or not DATABASE_URL,
    reason="MONGODB_TEST_URI and DATABASE_URL are required",
)


def test_phase12_real_migration_is_complete_resumable_and_immutable() -> None:
    async def scenario() -> None:
        database_name = f"case_phase12_test_{uuid4().hex}"
        client = AsyncMongoClient(MONGODB_TEST_URI, tz_aware=True)
        database = client[database_name]
        user_id, project_id, diagram_id, version_id = uuid4(), uuid4(), uuid4(), uuid4()
        try:
            await asegurar_esquema_mongo(database)
            snapshot = InstantaneaProyectoV2(
                captured_at=datetime.now(UTC),
                project=InstantaneaProyecto(id=project_id, name="Modelo academico"),
                diagrams=[
                    {
                        "id": str(diagram_id),
                        "classes": [
                            {
                                "name": "Curso",
                                "attributes": [{"name": "duracion", "type": "Integer"}],
                                "methods": [
                                    {"name": "agregarTema", "specification": {"steps": ["validar"]}}
                                ],
                            }
                        ],
                        "relationships": [
                            {
                                "type": "aggregation",
                                "source_multiplicity": "1",
                                "target_multiplicity": "*",
                            }
                        ],
                    }
                ],
            )
            with SessionLocal() as db:
                db.add_all(
                    [
                        Usuario(
                            id=user_id,
                            full_name="Phase 12",
                            email=f"phase12-{uuid4()}@example.com",
                            password_hash="unused",
                        ),
                        Proyecto(id=project_id, owner_id=user_id, name="Modelo academico"),
                    ]
                )
                db.flush()
                db.add_all(
                    [
                        IntegranteProyecto(
                            project_id=project_id, user_id=user_id, project_role="ORGANIZADOR"
                        ),
                        DiagramaUML(
                            id=diagram_id,
                            project_id=project_id,
                            created_by_user_id=user_id,
                            name="Modelo academico",
                        ),
                        VersionProyecto(
                            id=version_id,
                            project_id=project_id,
                            created_by_user_id=user_id,
                            version_number=1,
                            name="Base",
                            snapshot=snapshot.model_dump(mode="json"),
                            status="available",
                            kind="manual",
                            snapshot_schema_version=2,
                            snapshot_hash=hash_instantanea_sha256(snapshot),
                            snapshot_size_bytes=len(normalizar_instantanea_proyecto(snapshot)),
                            project_revision=4,
                        ),
                    ]
                )
                db.commit()

            migrator = MigradorVersionesUML(database, batch_size=10)
            first = await migrator.migrate(reset_checkpoint=True)
            replay = await migrator.migrate()
            stored = await database[ColeccionMongo.UML_DIAGRAM_VERSIONS.value].find_one(
                {"_id": str(version_id)}
            )

            assert first.consistent and first.migrated_versions == 1
            assert replay.consistent and replay.migrated_versions == 0
            assert "hash_contenido" in stored and "contenido" in stored
            stored = traducir_documento(stored, al_espanol=False)
            assert stored["content_hash"] == hash_instantanea_sha256(snapshot)
            assert stored["content"]["diagrams"][0]["classes"][0]["methods"][0][
                "specification"
            ] == {"steps": ["validar"]}
            assert stored["project_revision"] == 4
            immutable = await migrator.documents.get(version_id)
            assert immutable is not None
            with pytest.raises(ValueError, match="immutable UML version"):
                await migrator.documents.insertar_inmutable(
                    immutable.model_copy(update={"content_hash": "f" * 64})
                )
            checkpoint = await database[ColeccionMongo.MIGRATION_CHECKPOINTS.value].find_one(
                {"nombre_migracion": MIGRATION_NAME}
            )
            assert checkpoint["estado"] == "completed"
        finally:
            with SessionLocal() as db:
                db.execute(delete(VersionProyecto).where(VersionProyecto.project_id == project_id))
                db.execute(delete(DiagramaUML).where(DiagramaUML.project_id == project_id))
                db.execute(delete(IntegranteProyecto).where(IntegranteProyecto.project_id == project_id))
                db.execute(delete(Proyecto).where(Proyecto.id == project_id))
                db.execute(delete(Usuario).where(Usuario.id == user_id))
                db.commit()
            await client.drop_database(database_name)
            await client.close()

    asyncio.run(scenario())
