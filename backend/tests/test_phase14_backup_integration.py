import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from pymongo import AsyncMongoClient
from sqlalchemy import delete

from app.core.database.session import SessionLocal
from app.core.nosql.commands.coordinated_backup import CoordinatedBackupService
from app.core.nosql.contracts import MigrationCheckpointDocument, MongoCollection
from app.core.nosql.schema import ensure_mongo_schema
from app.modules.acceso_usuarios.models import User
from app.modules.proyectos_colaboracion.models import Project, ProjectMember

MONGODB_TEST_URI = os.getenv("MONGODB_TEST_URI")
DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not MONGODB_TEST_URI or not DATABASE_URL,
    reason="MONGODB_TEST_URI and DATABASE_URL are required",
)


def test_phase14_real_coordinated_backup_and_clean_restore() -> None:
    async def scenario() -> None:
        database_name = f"case_phase14_test_{uuid4().hex}"
        client = AsyncMongoClient(MONGODB_TEST_URI, tz_aware=True)
        database = client[database_name]
        user_id, project_id = uuid4(), uuid4()
        checkpoint_id = uuid5(NAMESPACE_URL, f"phase14-backup:{project_id}")
        try:
            await ensure_mongo_schema(database)
            with SessionLocal() as db:
                db.add(
                    User(
                        id=user_id,
                        full_name="Phase 14",
                        email=f"phase14-{uuid4()}@example.com",
                        password_hash="unused",
                    )
                )
                db.flush()
                db.add(Project(id=project_id, owner_id=user_id, name="Backup coordinado"))
                db.flush()
                db.add(
                    ProjectMember(
                        project_id=project_id,
                        user_id=user_id,
                        project_role="ORGANIZADOR",
                    )
                )
                db.commit()
            checkpoint = MigrationCheckpointDocument(
                _id=checkpoint_id,
                migration_name=f"phase14_backup_{project_id}",
                status="completed",
            )
            await database[MongoCollection.MIGRATION_CHECKPOINTS.value].insert_one(
                checkpoint.to_mongo()
            )

            with TemporaryDirectory() as temp:
                archive = Path(temp) / "coordinated.zip"
                service = CoordinatedBackupService(database)
                manifest = await service.create(archive)
                assert archive.exists() and archive.stat().st_size > 0
                assert manifest["postgresql"]["tables"]["projects"] >= 1
                assert (
                    manifest["mongodb"]["collections"][MongoCollection.MIGRATION_CHECKPOINTS.value]
                    == 1
                )

                await database[MongoCollection.MIGRATION_CHECKPOINTS.value].delete_many({})
                with SessionLocal() as db:
                    db.execute(delete(ProjectMember).where(ProjectMember.project_id == project_id))
                    db.execute(delete(Project).where(Project.id == project_id))
                    db.execute(delete(User).where(User.id == user_id))
                    db.commit()

                restored = await service.restore(archive, force=True)
                assert restored["backup_id"] == manifest["backup_id"]
                with SessionLocal() as db:
                    assert db.get(Project, project_id) is not None
                assert (
                    await database[MongoCollection.MIGRATION_CHECKPOINTS.value].find_one(
                        {"_id": str(checkpoint_id)}
                    )
                    is not None
                )
        finally:
            with SessionLocal() as db:
                db.execute(delete(ProjectMember).where(ProjectMember.project_id == project_id))
                db.execute(delete(Project).where(Project.id == project_id))
                db.execute(delete(User).where(User.id == user_id))
                db.commit()
            await client.drop_database(database_name)
            await client.close()

    asyncio.run(scenario())
