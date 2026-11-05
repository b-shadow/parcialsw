import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from pymongo import AsyncMongoClient
from sqlalchemy import delete

from app.core.database.sesion import SessionLocal
from app.core.nosql.commands.respaldo_coordinado import ServicioRespaldoCoordinado
from app.core.nosql.contratos import ColeccionMongo, DocumentoPuntoControlMigracion
from app.core.nosql.esquema import asegurar_esquema_mongo
from app.core.nosql.nombres_mongo import adaptar_mongo
from app.modules.acceso_usuarios.models import Usuario
from app.modules.proyectos_colaboracion.models import IntegranteProyecto, Proyecto

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
            await asegurar_esquema_mongo(database)
            with SessionLocal() as db:
                db.add(
                    Usuario(
                        id=user_id,
                        full_name="Phase 14",
                        email=f"phase14-{uuid4()}@example.com",
                        password_hash="unused",
                    )
                )
                db.flush()
                db.add(Proyecto(id=project_id, owner_id=user_id, name="Backup coordinado"))
                db.flush()
                db.add(
                    IntegranteProyecto(
                        project_id=project_id,
                        user_id=user_id,
                        project_role="ORGANIZADOR",
                    )
                )
                db.commit()
            checkpoint = DocumentoPuntoControlMigracion(
                _id=checkpoint_id,
                migration_name=f"phase14_backup_{project_id}",
                status="completed",
            )
            await adaptar_mongo(database)[ColeccionMongo.MIGRATION_CHECKPOINTS.value].insert_one(
                checkpoint.to_mongo()
            )

            with TemporaryDirectory() as temp:
                archive = Path(temp) / "coordinated.zip"
                service = ServicioRespaldoCoordinado(database)
                manifest = await service.create(archive)
                assert archive.exists() and archive.stat().st_size > 0
                assert manifest["postgresql"]["tables"]["proyectos"] >= 1
                assert (
                    manifest["mongodb"]["collections"][ColeccionMongo.MIGRATION_CHECKPOINTS.value]
                    == 1
                )

                await database[ColeccionMongo.MIGRATION_CHECKPOINTS.value].delete_many({})
                with SessionLocal() as db:
                    db.execute(delete(IntegranteProyecto).where(IntegranteProyecto.project_id == project_id))
                    db.execute(delete(Proyecto).where(Proyecto.id == project_id))
                    db.execute(delete(Usuario).where(Usuario.id == user_id))
                    db.commit()

                restored = await service.restore(archive, force=True)
                assert restored["backup_id"] == manifest["backup_id"]
                with SessionLocal() as db:
                    assert db.get(Proyecto, project_id) is not None
                assert (
                    await database[ColeccionMongo.MIGRATION_CHECKPOINTS.value].find_one(
                        {"_id": str(checkpoint_id)}
                    )
                    is not None
                )
        finally:
            with SessionLocal() as db:
                db.execute(delete(IntegranteProyecto).where(IntegranteProyecto.project_id == project_id))
                db.execute(delete(Proyecto).where(Proyecto.id == project_id))
                db.execute(delete(Usuario).where(Usuario.id == user_id))
                db.commit()
            await client.drop_database(database_name)
            await client.close()

    asyncio.run(scenario())
