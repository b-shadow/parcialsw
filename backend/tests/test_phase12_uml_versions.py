import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config.settings import settings
from app.core.nosql.client import MongoHealth
from app.core.nosql.contracts import MongoCollection, UmlDiagramVersionDocument
from app.core.nosql.outbox import NoSqlOutboxDispatcher
from app.main import app
from app.modules.proyectos_colaboracion.models import ProjectVersion
from app.modules.proyectos_colaboracion.schemas.snapshot import (
    ProjectSnapshotV2,
    SnapshotProject,
    snapshot_sha256,
)
from app.modules.proyectos_colaboracion.services.project_service import ProjectService
from app.modules.proyectos_colaboracion.services.version_document_store import (
    enqueue_version_document,
    version_document_from_sql,
)


def _snapshot(project_id, diagram_id):
    return ProjectSnapshotV2(
        captured_at=datetime.now(UTC),
        project=SnapshotProject(id=project_id, name="Academico"),
        diagrams=[
            {
                "id": str(diagram_id),
                "classes": [
                    {
                        "id": str(uuid4()),
                        "name": "Inscripcion",
                        "attributes": [{"name": "estado", "type": "String"}],
                        "methods": [
                            {
                                "name": "obtenerDetalle",
                                "return_type": "void",
                                "specification": {
                                    "preconditions": ["Existe"],
                                    "postconditions": ["Devuelve"],
                                },
                            }
                        ],
                        "position": {"x": 120, "y": 250},
                    }
                ],
                "relationships": [
                    {
                        "type": "association",
                        "source_multiplicity": "1",
                        "target_multiplicity": "*",
                    }
                ],
                "metadata_json": {"zoom": 1.25},
            }
        ],
    )


def _version(snapshot, project_id) -> ProjectVersion:
    now = datetime.now(UTC)
    return ProjectVersion(
        id=uuid4(),
        project_id=project_id,
        created_by_user_id=uuid4(),
        version_number=3,
        name="Entrega estable",
        description="Incluye especificaciones",
        snapshot=snapshot.model_dump(mode="json"),
        status="available",
        kind="manual",
        snapshot_schema_version=2,
        snapshot_hash=snapshot_sha256(snapshot),
        snapshot_size_bytes=1200,
        project_revision=7,
        created_at=now,
        updated_at=now,
    )


def test_phase12_document_preserves_complete_snapshot_and_registry_metadata() -> None:
    project_id, diagram_id = uuid4(), uuid4()
    snapshot = _snapshot(project_id, diagram_id)
    version = _version(snapshot, project_id)

    document = version_document_from_sql(version, diagram_id=diagram_id)
    restored = UmlDiagramVersionDocument.model_validate(document.to_mongo())

    assert restored.content == version.snapshot
    assert restored.project_revision == 7
    assert restored.snapshot_schema_version == 2
    assert restored.content_hash == snapshot_sha256(snapshot)
    method = restored.content["diagrams"][0]["classes"][0]["methods"][0]
    assert method["specification"]["preconditions"] == ["Existe"]
    assert restored.content["diagrams"][0]["relationships"][0]["target_multiplicity"] == "*"


def test_phase12_version_write_uses_transactional_outbox_without_commit() -> None:
    project_id, diagram_id = uuid4(), uuid4()
    version = _version(_snapshot(project_id, diagram_id), project_id)
    session = MagicMock()

    enqueue_version_document(session, version, diagram_id=diagram_id)

    session.flush.assert_called_once()
    session.commit.assert_not_called()
    event = session.add.call_args.args[0]
    assert event.payload["collection"] == MongoCollection.UML_DIAGRAM_VERSIONS.value
    assert event.payload["document"]["content"] == version.snapshot
    assert event.idempotency_key.endswith(version.snapshot_hash)


def test_phase12_preview_source_prefers_valid_mongodb_snapshot(monkeypatch) -> None:
    project_id, diagram_id = uuid4(), uuid4()
    snapshot = _snapshot(project_id, diagram_id)
    version = _version(snapshot, project_id)
    project = SimpleNamespace(id=project_id, name="Academico", description=None, owner_id=uuid4())
    service = object.__new__(ProjectService)
    service.db = MagicMock()
    service.version_documents = SimpleNamespace(
        safe_get=AsyncMock(return_value=version_document_from_sql(version, diagram_id=diagram_id))
    )
    monkeypatch.setattr(settings, "uml_versions_compare_reads", True)

    loaded, warnings = asyncio.run(service._load_version_snapshot(version, project))

    assert loaded == version.snapshot
    assert warnings == []


def test_phase12_hash_drift_falls_back_or_fails_by_flag(monkeypatch) -> None:
    project_id, diagram_id = uuid4(), uuid4()
    snapshot = _snapshot(project_id, diagram_id)
    version = _version(snapshot, project_id)
    document = version_document_from_sql(version, diagram_id=diagram_id).model_copy(
        update={"content_hash": "f" * 64}
    )
    project = SimpleNamespace(id=project_id, name="Academico", description=None, owner_id=uuid4())
    service = object.__new__(ProjectService)
    service.db = MagicMock()
    service.version_documents = SimpleNamespace(safe_get=AsyncMock(return_value=document))
    monkeypatch.setattr(settings, "uml_versions_compare_reads", True)
    monkeypatch.setattr(settings, "uml_versions_sql_fallback_enabled", True)

    loaded, warnings = asyncio.run(service._load_version_snapshot(version, project))
    assert loaded == version.snapshot
    assert warnings == ["mongodb_snapshot_hash_mismatch_fallback_sql"]

    monkeypatch.setattr(settings, "uml_versions_sql_fallback_enabled", False)
    with pytest.raises(HTTPException) as rejected:
        asyncio.run(service._load_version_snapshot(version, project))
    assert rejected.value.detail["code"] == "VERSION_DOCUMENT_DIVERGED"


def test_phase12_outbox_rejects_mutation_of_immutable_version() -> None:
    project_id, diagram_id = uuid4(), uuid4()
    version = _version(_snapshot(project_id, diagram_id), project_id)
    document = version_document_from_sql(version, diagram_id=diagram_id)
    target = SimpleNamespace(
        find_one=AsyncMock(return_value={"_id": str(version.id), "content_hash": "f" * 64}),
        insert_one=AsyncMock(),
    )
    receipts = SimpleNamespace(find_one=AsyncMock(return_value=None), insert_one=AsyncMock())
    database = {
        MongoCollection.UML_DIAGRAM_VERSIONS.value: target,
        MongoCollection.PROCESSED_EVENTS.value: receipts,
    }
    event = SimpleNamespace(
        id=uuid4(),
        idempotency_key="immutable-conflict",
        payload={
            "collection": MongoCollection.UML_DIAGRAM_VERSIONS.value,
            "operation": "upsert",
            "document_id": str(version.id),
            "document": document.to_mongo(),
        },
    )

    with pytest.raises(ValueError, match="immutable UML version"):
        asyncio.run(NoSqlOutboxDispatcher(MagicMock(), database)._apply(event))
    target.insert_one.assert_not_awaited()
    receipts.insert_one.assert_not_awaited()


def test_phase12_readiness_requires_completed_uml_version_migration(monkeypatch) -> None:
    collection = SimpleNamespace(find_one=AsyncMock(return_value={"status": "completed"}))
    database = {MongoCollection.MIGRATION_CHECKPOINTS.value: collection}
    health = MongoHealth(status="available", required=True, database="case_test")
    monkeypatch.setattr(settings, "uml_versions_migration_required", True)

    with (
        patch("app.main.SessionLocal", MagicMock()),
        patch.object(app.state.mongo_manager, "ping", AsyncMock(return_value=health)),
        patch.object(app.state.mongo_manager, "_database", database),
    ):
        response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json()["components"]["uml_version_migration"] == {
        "status": "completed",
        "required": True,
    }


def test_phase12_restore_replay_is_idempotent_and_does_not_read_snapshot() -> None:
    project_id, user_id = uuid4(), uuid4()
    source_id, backup_id, operation_id = uuid4(), uuid4(), uuid4()
    project = SimpleNamespace(id=project_id, owner_id=user_id, revision=8)
    source = SimpleNamespace(
        id=source_id,
        project_id=project_id,
        version_number=2,
        created_by_user_id=user_id,
        name="Objetivo",
        description=None,
        status="available",
        created_at=datetime.now(UTC),
        kind="manual",
        snapshot_schema_version=2,
        snapshot_hash="a" * 64,
        snapshot_size_bytes=100,
        project_revision=4,
        snapshot={},
    )
    backup = SimpleNamespace(
        id=backup_id,
        project_id=project_id,
        version_number=3,
        created_by_user_id=user_id,
        name="Respaldo",
        description=None,
        status="available",
        created_at=datetime.now(UTC),
        kind="pre_restore_backup",
        snapshot_schema_version=2,
        snapshot_hash="b" * 64,
        snapshot_size_bytes=100,
        project_revision=8,
        snapshot={},
    )
    operation = SimpleNamespace(
        id=operation_id,
        source_version_id=source_id,
        backup_version_id=backup_id,
        status="completed",
        diagnostics_json={"restored_diagram_ids": []},
        project_revision_after=9,
        project_revision_before=8,
    )
    service = object.__new__(ProjectService)
    service.db = SimpleNamespace(scalar=lambda _statement: operation)
    service.mutations = SimpleNamespace(acquire=lambda _project_id: project)
    service.projects = SimpleNamespace(
        get_version=lambda version_id: source if version_id == source_id else backup
    )
    service.version_documents = SimpleNamespace(safe_get=AsyncMock())

    result = asyncio.run(
        service.restore_version(project_id, source_id, user_id, idempotency_key="same-request")
    )

    assert result["idempotent_replay"] is True
    assert result["backup_version"]["id"] == backup_id
    service.version_documents.safe_get.assert_not_awaited()
