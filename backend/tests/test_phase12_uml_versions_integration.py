import asyncio
import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient
from sqlalchemy import delete

from app.core.database.session import SessionLocal
from app.core.nosql.commands.migrate_uml_versions import (
    MIGRATION_NAME,
    UmlVersionMigrator,
)
from app.core.nosql.contracts import MongoCollection
from app.core.nosql.schema import ensure_mongo_schema
from app.modules.acceso_usuarios.models import User
from app.modules.modelado_uml.models import UmlDiagram
from app.modules.proyectos_colaboracion.models import Project, ProjectMember, ProjectVersion
from app.modules.proyectos_colaboracion.schemas.snapshot import (
    ProjectSnapshotV2,
    SnapshotProject,
    canonicalize_project_snapshot,
    snapshot_sha256,
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
            await ensure_mongo_schema(database)
            snapshot = ProjectSnapshotV2(
                captured_at=datetime.now(UTC),
                project=SnapshotProject(id=project_id, name="Modelo academico"),
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
                        User(
                            id=user_id,
                            full_name="Phase 12",
                            email=f"phase12-{uuid4()}@example.com",
                            password_hash="unused",
                        ),
                        Project(id=project_id, owner_id=user_id, name="Modelo academico"),
                    ]
                )
                db.flush()
                db.add_all(
                    [
                        ProjectMember(
                            project_id=project_id, user_id=user_id, project_role="ORGANIZADOR"
                        ),
                        UmlDiagram(
                            id=diagram_id,
                            project_id=project_id,
                            created_by_user_id=user_id,
                            name="Modelo academico",
                        ),
                        ProjectVersion(
                            id=version_id,
                            project_id=project_id,
                            created_by_user_id=user_id,
                            version_number=1,
                            name="Base",
                            snapshot=snapshot.model_dump(mode="json"),
                            status="available",
                            kind="manual",
                            snapshot_schema_version=2,
                            snapshot_hash=snapshot_sha256(snapshot),
                            snapshot_size_bytes=len(canonicalize_project_snapshot(snapshot)),
                            project_revision=4,
                        ),
                    ]
                )
                db.commit()

            migrator = UmlVersionMigrator(database, batch_size=10)
            first = await migrator.migrate(reset_checkpoint=True)
            replay = await migrator.migrate()
            stored = await database[MongoCollection.UML_DIAGRAM_VERSIONS.value].find_one(
                {"_id": str(version_id)}
            )

            assert first.consistent and first.migrated_versions == 1
            assert replay.consistent and replay.migrated_versions == 0
            assert stored["content_hash"] == snapshot_sha256(snapshot)
            assert stored["content"]["diagrams"][0]["classes"][0]["methods"][0][
                "specification"
            ] == {"steps": ["validar"]}
            assert stored["project_revision"] == 4
            immutable = await migrator.documents.get(version_id)
            assert immutable is not None
            with pytest.raises(ValueError, match="immutable UML version"):
                await migrator.documents.insert_immutable(
                    immutable.model_copy(update={"content_hash": "f" * 64})
                )
            checkpoint = await database[MongoCollection.MIGRATION_CHECKPOINTS.value].find_one(
                {"migration_name": MIGRATION_NAME}
            )
            assert checkpoint["status"] == "completed"
        finally:
            with SessionLocal() as db:
                db.execute(delete(ProjectVersion).where(ProjectVersion.project_id == project_id))
                db.execute(delete(UmlDiagram).where(UmlDiagram.project_id == project_id))
                db.execute(delete(ProjectMember).where(ProjectMember.project_id == project_id))
                db.execute(delete(Project).where(Project.id == project_id))
                db.execute(delete(User).where(User.id == user_id))
                db.commit()
            await client.drop_database(database_name)
            await client.close()

    asyncio.run(scenario())
