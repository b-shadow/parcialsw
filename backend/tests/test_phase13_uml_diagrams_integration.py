import asyncio
import os
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient
from sqlalchemy import delete

from app.core.database.session import SessionLocal
from app.core.nosql.commands.migrate_uml_diagrams import (
    MIGRATION_NAME,
    ActiveUmlDiagramMigrator,
)
from app.core.nosql.contracts import MongoCollection
from app.core.nosql.outbox import NoSqlOutboxDispatcher
from app.core.nosql.outbox_model import NoSqlOutboxEvent
from app.core.nosql.reconciliation import canonical_sha256
from app.core.nosql.repositories import UmlDiagramRepository
from app.core.nosql.schema import ensure_mongo_schema
from app.modules.acceso_usuarios.models import AuditLog, User
from app.modules.modelado_uml.models import (
    UmlAttribute,
    UmlClass,
    UmlDiagram,
    UmlMethod,
    UmlMethodSpecification,
    UmlParameter,
    UmlRelationship,
    UmlVisualElement,
)
from app.modules.modelado_uml.schemas.uml import UmlClassUpdateRequest
from app.modules.modelado_uml.services.uml_service import UmlService
from app.modules.proyectos_colaboracion.models import Project, ProjectMember

MONGODB_TEST_URI = os.getenv("MONGODB_TEST_URI")
DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not MONGODB_TEST_URI or not DATABASE_URL,
    reason="MONGODB_TEST_URI and DATABASE_URL are required",
)


def test_phase13_real_migration_outbox_and_optimistic_concurrency() -> None:
    async def scenario() -> None:
        database_name = f"case_phase13_test_{uuid4().hex}"
        client = AsyncMongoClient(MONGODB_TEST_URI, tz_aware=True)
        database = client[database_name]
        user_id, project_id, diagram_id = uuid4(), uuid4(), uuid4()
        student_id, course_id, method_id = uuid4(), uuid4(), uuid4()
        try:
            await ensure_mongo_schema(database)
            with SessionLocal() as db:
                db.add_all(
                    [
                        User(
                            id=user_id,
                            full_name="Phase 13",
                            email=f"phase13-{uuid4()}@example.com",
                            password_hash="unused",
                        ),
                        Project(
                            id=project_id,
                            owner_id=user_id,
                            name="Modelo academico",
                            revision=4,
                        ),
                    ]
                )
                db.flush()
                db.add_all(
                    [
                        ProjectMember(
                            project_id=project_id,
                            user_id=user_id,
                            project_role="ORGANIZADOR",
                        ),
                        UmlDiagram(
                            id=diagram_id,
                            project_id=project_id,
                            created_by_user_id=user_id,
                            name="Modelo academico",
                        ),
                        UmlClass(id=student_id, diagram_id=diagram_id, name="Estudiante"),
                        UmlClass(id=course_id, diagram_id=diagram_id, name="Curso"),
                    ]
                )
                db.flush()
                db.add_all(
                    [
                        UmlAttribute(
                            class_id=student_id,
                            name="correo",
                            data_type="String",
                            is_required=True,
                        ),
                        UmlMethod(
                            id=method_id,
                            class_id=student_id,
                            name="inscribirse",
                            return_type="void",
                        ),
                        UmlRelationship(
                            diagram_id=diagram_id,
                            source_class_id=student_id,
                            target_class_id=course_id,
                            relationship_type="association",
                            source_cardinality="*",
                            target_cardinality="1",
                            label="inscripcion",
                        ),
                        UmlVisualElement(
                            diagram_id=diagram_id,
                            element_type="class",
                            element_id=student_id,
                            position_x=80,
                            position_y=120,
                        ),
                        UmlVisualElement(
                            diagram_id=diagram_id,
                            element_type="class",
                            element_id=course_id,
                            position_x=440,
                            position_y=120,
                        ),
                    ]
                )
                db.flush()
                db.add_all(
                    [
                        UmlParameter(
                            method_id=method_id,
                            name="cursoId",
                            data_type="UUID",
                        ),
                        UmlMethodSpecification(
                            method_id=method_id,
                            description="Inscribe al estudiante",
                            operation_kind="business_action",
                            exposure="api",
                            preconditions=["El curso existe"],
                            postconditions=["La inscripcion fue registrada"],
                        ),
                    ]
                )
                db.commit()

            migrator = ActiveUmlDiagramMigrator(database, batch_size=10)
            first = await migrator.migrate(reset_checkpoint=True)
            replay = await migrator.migrate()
            stored = await database[MongoCollection.UML_DIAGRAMS.value].find_one(
                {"_id": str(diagram_id)}
            )

            assert first.consistent and first.migrated_diagrams == 1
            assert replay.consistent and replay.migrated_diagrams == 0
            assert stored["revision"] == 4
            assert stored["content_hash"] == canonical_sha256(stored["content"])
            student = next(
                item for item in stored["content"]["classes"] if item["name"] == "Estudiante"
            )
            assert student["attributes"][0]["name"] == "correo"
            assert student["methods"][0]["parameters"][0]["name"] == "cursoId"
            assert student["methods"][0]["specification"]["preconditions"] == ["El curso existe"]
            assert stored["content"]["relationships"][0]["target_cardinality"] == "1"

            with SessionLocal() as db:
                UmlService(db).update_class(
                    student_id,
                    UmlClassUpdateRequest(name="Alumno"),
                    user_id,
                )
            with SessionLocal() as db:
                dispatched = await NoSqlOutboxDispatcher(db, database).dispatch(limit=20)
            assert dispatched["dead"] == 0
            updated = await database[MongoCollection.UML_DIAGRAMS.value].find_one(
                {"_id": str(diagram_id)}
            )
            assert updated["revision"] == 5
            assert any(item["name"] == "Alumno" for item in updated["content"]["classes"])

            repository = UmlDiagramRepository(database)
            current = await repository.get(diagram_id)
            assert current is not None
            changed_content = dict(current.content)
            changed_content["metadata_json"] = {"zoom": 1.25}
            changed = current.model_copy(
                update={
                    "revision": 6,
                    "content": changed_content,
                    "content_hash": canonical_sha256(changed_content),
                }
            )
            assert await repository.replace_if_revision(changed, expected_revision=5)
            assert await repository.replace_if_revision(changed, expected_revision=5) is None

            checkpoint = await database[MongoCollection.MIGRATION_CHECKPOINTS.value].find_one(
                {"migration_name": MIGRATION_NAME}
            )
            assert checkpoint["status"] == "completed"
        finally:
            with SessionLocal() as db:
                db.execute(
                    delete(NoSqlOutboxEvent).where(NoSqlOutboxEvent.aggregate_id == diagram_id)
                )
                db.execute(delete(AuditLog).where(AuditLog.project_id == project_id))
                db.execute(
                    delete(UmlMethodSpecification).where(
                        UmlMethodSpecification.method_id == method_id
                    )
                )
                db.execute(delete(UmlParameter).where(UmlParameter.method_id == method_id))
                db.execute(delete(UmlMethod).where(UmlMethod.class_id.in_([student_id, course_id])))
                db.execute(
                    delete(UmlAttribute).where(UmlAttribute.class_id.in_([student_id, course_id]))
                )
                db.execute(delete(UmlRelationship).where(UmlRelationship.diagram_id == diagram_id))
                db.execute(
                    delete(UmlVisualElement).where(UmlVisualElement.diagram_id == diagram_id)
                )
                db.execute(delete(UmlClass).where(UmlClass.diagram_id == diagram_id))
                db.execute(delete(UmlDiagram).where(UmlDiagram.id == diagram_id))
                db.execute(delete(ProjectMember).where(ProjectMember.project_id == project_id))
                db.execute(delete(Project).where(Project.id == project_id))
                db.execute(delete(User).where(User.id == user_id))
                db.commit()
            await client.drop_database(database_name)
            await client.close()

    asyncio.run(scenario())
