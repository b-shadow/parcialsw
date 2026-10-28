import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config.settings import settings
from app.core.nosql.client import MongoHealth
from app.core.nosql.contracts import MongoCollection, UmlDiagramDocument
from app.core.nosql.outbox import NoSqlOutboxDispatcher
from app.core.nosql.reconciliation import canonical_sha256
from app.core.nosql.repositories import UmlDiagramRepository
from app.main import app
from app.modules.modelado_uml.engine.internal_model import UmlDiagramModel
from app.modules.modelado_uml.services.active_diagram_store import (
    ActiveUmlDocumentStore,
    canonical_uml_content,
)


def _content(diagram_id=None, project_id=None):
    diagram_id = diagram_id or uuid4()
    project_id = project_id or uuid4()
    source_id, target_id = uuid4(), uuid4()
    return {
        "id": str(diagram_id),
        "project_id": str(project_id),
        "name": "Academico",
        "classes": [
            {
                "id": str(target_id),
                "name": "Curso",
                "attributes": [],
                "methods": [],
                "visual": {"id": str(uuid4()), "x": 450, "y": 80},
            },
            {
                "id": str(source_id),
                "name": "Estudiante",
                "attributes": [
                    {
                        "id": str(uuid4()),
                        "name": "correo",
                        "data_type": "String",
                        "order_index": 0,
                    }
                ],
                "methods": [
                    {
                        "id": str(uuid4()),
                        "name": "inscribirse",
                        "return_type": "void",
                        "parameters": [
                            {
                                "id": str(uuid4()),
                                "name": "cursoId",
                                "data_type": "UUID",
                                "order_index": 0,
                            }
                        ],
                        "specification": {
                            "description": "Inscribe al estudiante",
                            "preconditions": ["El curso existe"],
                        },
                    }
                ],
                "visual": {"id": str(uuid4()), "x": 80, "y": 80},
            },
        ],
        "relationships": [
            {
                "id": str(uuid4()),
                "source_class_id": str(source_id),
                "target_class_id": str(target_id),
                "relationship_type": "association",
                "source_cardinality": "*",
                "target_cardinality": "1",
                "label": "inscripcion",
            }
        ],
    }


def _document(*, revision=4, content=None):
    raw = canonical_uml_content(content or _content())
    return UmlDiagramDocument(
        _id=raw["id"],
        project_id=raw["project_id"],
        revision=revision,
        content=raw,
        content_hash=canonical_sha256(raw),
    )


def test_phase13_canonical_document_preserves_complete_uml_and_stable_hash() -> None:
    document = _document()
    reparsed = UmlDiagramModel.model_validate(document.content)

    assert [item.name for item in reparsed.classes] == ["Curso", "Estudiante"]
    method = reparsed.classes[1].methods[0]
    assert method.parameters[0].name == "cursoId"
    assert method.specification["preconditions"] == ["El curso existe"]
    assert reparsed.classes[1].visual.x == 80
    assert reparsed.relationships[0].target_cardinality == "1"
    assert document.content_hash == canonical_sha256(canonical_uml_content(reparsed))


def test_phase13_repository_requires_exact_revision_and_valid_references() -> None:
    document = _document(revision=5)
    collection = SimpleNamespace(find_one_and_replace=AsyncMock(return_value=document.to_mongo()))
    repository = UmlDiagramRepository({MongoCollection.UML_DIAGRAMS.value: collection})

    stored = asyncio.run(repository.replace_if_revision(document, expected_revision=4))

    assert stored is not None and stored.revision == 5
    assert collection.find_one_and_replace.await_args.args[0] == {
        "_id": str(document.id),
        "revision": 4,
    }
    with pytest.raises(ValueError, match="increment expected_revision"):
        asyncio.run(repository.replace_if_revision(document, expected_revision=3))

    invalid_content = _content()
    invalid_content["relationships"][0]["target_class_id"] = str(uuid4())
    invalid = _document(revision=5, content=invalid_content)
    with pytest.raises(ValueError, match="destino inexistente"):
        asyncio.run(repository.replace_if_revision(invalid, expected_revision=4))


def test_phase13_store_reads_mongodb_and_uses_sql_for_pending_outbox(monkeypatch) -> None:
    document = _document(revision=8)
    diagram = SimpleNamespace(id=document.id, project_id=document.project_id)
    sql_model = UmlDiagramModel(
        id=str(document.id),
        project_id=str(document.project_id),
        name="SQL pendiente",
    )
    collection = SimpleNamespace(find_one=lambda _query: document.to_mongo())
    store = ActiveUmlDocumentStore(database={MongoCollection.UML_DIAGRAMS.value: collection})
    db = MagicMock()
    db.scalar.return_value = 8
    monkeypatch.setattr(settings, "uml_diagrams_mongodb_read_enabled", True)
    monkeypatch.setattr(settings, "uml_diagrams_sql_fallback_enabled", True)
    monkeypatch.setattr(settings, "uml_diagrams_compare_reads", False)

    with patch(
        "app.modules.modelado_uml.services.active_diagram_store.build_sql_diagram_model",
        return_value=sql_model,
    ):
        selected = store.model_for(db, diagram)
        assert selected.name == "Academico"

        db.scalar.return_value = 9
        selected = store.model_for(db, diagram)
        assert selected.name == "SQL pendiente"


def test_phase13_outbox_never_overwrites_newer_revision() -> None:
    incoming = _document(revision=6)
    newer = incoming.model_copy(update={"revision": 7}).to_mongo()
    target = SimpleNamespace(
        find_one=AsyncMock(return_value=newer),
        replace_one=AsyncMock(),
        insert_one=AsyncMock(),
    )
    receipts = SimpleNamespace(find_one=AsyncMock(return_value=None), insert_one=AsyncMock())
    event = SimpleNamespace(
        id=uuid4(),
        idempotency_key="uml-revision-6",
        payload={
            "collection": MongoCollection.UML_DIAGRAMS.value,
            "operation": "upsert",
            "document_id": str(incoming.id),
            "document": incoming.to_mongo(),
        },
    )

    asyncio.run(
        NoSqlOutboxDispatcher(
            MagicMock(),
            {
                MongoCollection.UML_DIAGRAMS.value: target,
                MongoCollection.PROCESSED_EVENTS.value: receipts,
            },
        )._apply(event)
    )

    target.replace_one.assert_not_awaited()
    receipts.insert_one.assert_awaited_once()


def test_phase13_outbox_patches_changed_class_by_id() -> None:
    previous = _document(revision=5)
    changed_content = previous.model_copy(deep=True).content
    changed_content["classes"][0]["name"] = "Asignatura"
    incoming = previous.model_copy(
        update={
            "revision": 6,
            "content": changed_content,
            "content_hash": canonical_sha256(changed_content),
            "updated_at": datetime.now(UTC),
        }
    )
    target = SimpleNamespace(
        find_one=AsyncMock(return_value=previous.to_mongo()),
        update_one=AsyncMock(return_value=SimpleNamespace(matched_count=1)),
        replace_one=AsyncMock(),
        insert_one=AsyncMock(),
    )
    receipts = SimpleNamespace(find_one=AsyncMock(return_value=None), insert_one=AsyncMock())
    event = SimpleNamespace(
        id=uuid4(),
        idempotency_key="uml-partial-revision-6",
        payload={
            "collection": MongoCollection.UML_DIAGRAMS.value,
            "operation": "upsert",
            "document_id": str(incoming.id),
            "document": incoming.to_mongo(),
        },
    )

    asyncio.run(
        NoSqlOutboxDispatcher(
            MagicMock(),
            {
                MongoCollection.UML_DIAGRAMS.value: target,
                MongoCollection.PROCESSED_EVENTS.value: receipts,
            },
        )._apply(event)
    )

    target.replace_one.assert_not_awaited()
    update_filter, operation = target.update_one.await_args.args
    assert update_filter == {"_id": str(incoming.id), "revision": 5}
    assert operation["$set"]["revision"] == 6
    assert any(path.startswith("content.classes.$[") for path in operation["$set"])
    assert target.update_one.await_args.kwargs["array_filters"]


def test_phase13_readiness_requires_completed_active_diagram_migration(monkeypatch) -> None:
    collection = SimpleNamespace(find_one=AsyncMock(return_value={"status": "completed"}))
    health = MongoHealth(status="available", required=True, database="case_test")
    monkeypatch.setattr(settings, "uml_diagrams_migration_required", True)

    with (
        patch("app.main.SessionLocal", MagicMock()),
        patch.object(app.state.mongo_manager, "ping", AsyncMock(return_value=health)),
        patch.object(
            app.state.mongo_manager,
            "_database",
            {MongoCollection.MIGRATION_CHECKPOINTS.value: collection},
        ),
    ):
        response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json()["components"]["uml_diagram_migration"] == {
        "status": "completed",
        "required": True,
    }
