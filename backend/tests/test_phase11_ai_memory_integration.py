import asyncio
import os
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient
from sqlalchemy import delete, func, select

from app.core.database.session import SessionLocal
from app.core.nosql.commands.migrate_ai_memory import MIGRATION_NAME, AiMemoryMigrator
from app.core.nosql.contracts import MongoCollection
from app.core.nosql.outbox_model import NoSqlOutboxEvent
from app.core.nosql.schema import ensure_mongo_schema
from app.modules.acceso_usuarios.models import User
from app.modules.asistente_proyecto.models import AiConversation, AiMessage
from app.modules.asistente_proyecto.schemas import AiMessageCreateInternal
from app.modules.asistente_proyecto.services.assistant_service import AssistantContractService
from app.modules.proyectos_colaboracion.models import Project, ProjectMember

MONGODB_TEST_URI = os.getenv("MONGODB_TEST_URI")
DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not MONGODB_TEST_URI or not DATABASE_URL,
    reason="MONGODB_TEST_URI and DATABASE_URL are required",
)


def test_phase11_real_postgresql_mongodb_migration_and_idempotency() -> None:
    async def scenario() -> None:
        database_name = f"case_phase11_test_{uuid4().hex}"
        client = AsyncMongoClient(MONGODB_TEST_URI, tz_aware=True)
        database = client[database_name]
        user_id = uuid4()
        project_id = uuid4()
        conversation_id = uuid4()
        client_message_id = uuid4()
        try:
            await ensure_mongo_schema(database)
            with SessionLocal() as db:
                user = User(
                    id=user_id,
                    full_name="Phase 11",
                    email=f"phase11-{uuid4()}@example.com",
                    password_hash="not-used",
                )
                project = Project(
                    id=project_id,
                    owner_id=user_id,
                    name="Migración de memoria",
                    description="Prueba poliglota",
                )
                member = ProjectMember(
                    project_id=project_id,
                    user_id=user_id,
                    project_role="ORGANIZADOR",
                )
                conversation = AiConversation(
                    id=conversation_id,
                    project_id=project_id,
                    created_by_user_id=user_id,
                    title="Revisión del modelo",
                    summary='{"project_goal":"Validar memoria"}',
                    summary_until_sequence=1,
                )
                db.add_all([user, project, member, conversation])
                db.commit()

                service = AssistantContractService(db)
                first, created = service.create_message(
                    project_id,
                    user_id,
                    AiMessageCreateInternal(
                        role="user",
                        content="Revisa el diagrama sin duplicar este mensaje",
                        client_message_id=client_message_id,
                        correlation_id=uuid4(),
                    ),
                    conversation_id,
                )
                replay, replay_created = service.create_message(
                    project_id,
                    user_id,
                    AiMessageCreateInternal(
                        role="user",
                        content="Revisa el diagrama sin duplicar este mensaje",
                        client_message_id=client_message_id,
                        correlation_id=uuid4(),
                    ),
                    conversation_id,
                )
                assert created is True
                assert replay_created is False
                assert replay.id == first.id
                outbox_count = db.scalar(
                    select(func.count(NoSqlOutboxEvent.id)).where(
                        NoSqlOutboxEvent.aggregate_id == first.id
                    )
                )
                assert outbox_count == 1

            migrator = AiMemoryMigrator(database, batch_size=10)
            first_report = await migrator.migrate(reset_checkpoint=True)
            replay_report = await migrator.migrate()

            assert first_report.consistent
            assert first_report.migrated_messages >= 1
            assert first_report.migrated_contexts >= 1
            assert replay_report.consistent
            assert replay_report.migrated_messages == 0

            stored = await database[MongoCollection.AI_MESSAGES.value].find_one(
                {"_id": str(first.id)}
            )
            assert stored["content"] == "Revisa el diagrama sin duplicar este mensaje"
            assert stored["sequence_number"] == 1
            assert len(stored["content_hash"]) == 64
            checkpoint = await database[MongoCollection.MIGRATION_CHECKPOINTS.value].find_one(
                {"migration_name": MIGRATION_NAME}
            )
            assert checkpoint["status"] == "completed"
        finally:
            with SessionLocal() as db:
                message_ids = list(
                    db.scalars(select(AiMessage.id).where(AiMessage.project_id == project_id))
                )
                if message_ids:
                    db.execute(
                        delete(NoSqlOutboxEvent).where(
                            NoSqlOutboxEvent.aggregate_id.in_(message_ids)
                        )
                    )
                db.execute(delete(AiMessage).where(AiMessage.project_id == project_id))
                db.execute(delete(AiConversation).where(AiConversation.project_id == project_id))
                db.execute(delete(ProjectMember).where(ProjectMember.project_id == project_id))
                db.execute(delete(Project).where(Project.id == project_id))
                db.execute(delete(User).where(User.id == user_id))
                db.commit()
            await client.drop_database(database_name)
            await client.close()

    asyncio.run(scenario())
