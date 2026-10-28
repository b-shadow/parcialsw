import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config.settings import settings
from app.core.nosql.client import MongoHealth
from app.core.nosql.commands.consolidate import ConsolidationGate
from app.core.nosql.commands.coordinated_backup import _decode, _encode
from app.core.nosql.contracts import MongoCollection
from app.core.nosql.reconciliation import ReconciliationService, canonical_sha256
from app.main import app
from app.modules.modelado_uml.engine.internal_model import UmlDiagramModel
from app.modules.modelado_uml.models import UmlDiagram
from app.modules.modelado_uml.repositories.mongo_uml_repository import MongoUmlRepository
from app.modules.modelado_uml.services.active_diagram_store import (
    SYNC_PROJECTS_KEY,
    ActiveUmlDocumentStore,
    mark_uml_project_for_sync,
)


class AsyncCursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def __aiter__(self):
        self.iterator = iter(self.rows)
        return self

    async def __anext__(self):
        try:
            return next(self.iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    def sort(self, *_args, **_kwargs):
        return self


class FakeCollection:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.insert_one = AsyncMock()

    def find(self, *_args, **_kwargs):
        return AsyncCursor(self.rows)

    async def index_information(self):
        return {"_id_": {"key": [("_id", 1)]}}

    async def find_one(self, *_args, **_kwargs):
        return self.rows[0] if self.rows else None

    async def count_documents(self, *_args, **_kwargs):
        return len(self.rows)

    async def find_one_and_replace(self, _filter, payload, **_kwargs):
        return payload


class FakeDatabase(dict):
    async def command(self, _command):
        return {"ok": 1}


def _uml_document(diagram_id, project_id, *, revision=3):
    content = UmlDiagramModel(
        id=str(diagram_id),
        project_id=str(project_id),
        name="Consolidado",
    ).model_dump(mode="json")
    return {
        "_id": str(diagram_id),
        "project_id": str(project_id),
        "schema_version": 1,
        "revision": revision,
        "content": content,
        "content_hash": canonical_sha256(content),
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


def test_phase14_strict_uml_read_never_builds_sql_projection(monkeypatch) -> None:
    diagram_id, project_id = uuid4(), uuid4()
    document = _uml_document(diagram_id, project_id)
    store = ActiveUmlDocumentStore(
        database={
            MongoCollection.UML_DIAGRAMS.value: SimpleNamespace(find_one=lambda _query: document)
        }
    )
    db = MagicMock()
    db.scalar.return_value = 3
    diagram = SimpleNamespace(id=diagram_id, project_id=project_id)
    monkeypatch.setattr(settings, "uml_diagrams_mongodb_read_enabled", True)
    monkeypatch.setattr(settings, "uml_diagrams_sql_fallback_enabled", False)
    monkeypatch.setattr(settings, "uml_diagrams_compare_reads", False)

    with patch(
        "app.modules.modelado_uml.services.active_diagram_store.build_sql_diagram_model"
    ) as sql_projection:
        model = store.model_for(db, diagram)

    assert model.name == "Consolidado"
    sql_projection.assert_not_called()


def test_phase14_operational_audit_detects_revision_lag_and_persists(monkeypatch) -> None:
    project_id, diagram_id = uuid4(), uuid4()
    database = FakeDatabase(
        {
            MongoCollection.UML_DIAGRAMS.value: FakeCollection(
                [_uml_document(diagram_id, project_id, revision=2)]
            ),
            MongoCollection.UML_DIAGRAM_VERSIONS.value: FakeCollection(),
            MongoCollection.AI_MESSAGES.value: FakeCollection(),
            MongoCollection.AI_CONTEXT_SNAPSHOTS.value: FakeCollection(),
            MongoCollection.OPERATIONAL_AUDITS.value: FakeCollection(),
        }
    )
    db = MagicMock()
    db.execute.side_effect = [
        SimpleNamespace(tuples=lambda: [(project_id, 3)]),
        SimpleNamespace(tuples=lambda: [(diagram_id, project_id)]),
        SimpleNamespace(tuples=list),
        SimpleNamespace(tuples=list),
    ]
    db.scalars.side_effect = [[], []]
    monkeypatch.setattr(settings, "nosql_alert_max_revision_lag", 0)

    report = asyncio.run(ReconciliationService(db, database).audit_operational())

    assert report["status"] == "degraded"
    assert any(item["code"] == "REVISION_LAG" for item in report["findings"])
    assert report["metrics"]["max_revision_lag"] == 1
    database[MongoCollection.OPERATIONAL_AUDITS.value].insert_one.assert_awaited_once()


def test_phase14_backup_encoding_roundtrip_preserves_database_types() -> None:
    value = {
        "id": uuid4(),
        "created_at": datetime.now(UTC),
        "amount": Decimal("19.95"),
        "payload": b"case-inteligente",
        "nested": [{"enabled": True}],
        "user_json": {"__case_type__": "uuid", "value": "not-a-backup-tag"},
    }

    assert _decode(_encode(value)) == value


def test_phase14_consolidated_mode_keeps_canonical_publication_when_dual_write_is_off(
    monkeypatch,
) -> None:
    project_id = uuid4()
    db = SimpleNamespace(info={})
    monkeypatch.setattr(settings, "uml_diagrams_dual_write_enabled", False)
    monkeypatch.setattr(settings, "nosql_consolidated_mode", True)

    mark_uml_project_for_sync(db, project_id)

    assert db.info[SYNC_PROJECTS_KEY] == {project_id}


def test_phase14_document_repository_roundtrips_embedded_uml_content() -> None:
    project_id, diagram_id, class_id, attribute_id, method_id, parameter_id = (
        uuid4() for _ in range(6)
    )
    diagram = UmlDiagram(
        id=diagram_id,
        project_id=project_id,
        created_by_user_id=uuid4(),
        name="Ventas",
        diagram_type="class",
        status="active",
        current_version=1,
        metadata_json={},
    )
    source = UmlDiagramModel.model_validate({
        "id": str(diagram_id),
        "project_id": str(project_id),
        "name": "Ventas",
        "classes": [{
            "id": str(class_id),
            "name": "Cliente",
            "attributes": [{
                "id": str(attribute_id),
                "name": "correo",
                "data_type": "String",
            }],
            "methods": [{
                "id": str(method_id),
                "name": "registrar",
                "return_type": "void",
                "parameters": [{
                    "id": str(parameter_id),
                    "name": "email",
                    "data_type": "String",
                }],
            }],
            "visual": {"x": 120, "y": 80},
        }],
    })
    repository = MongoUmlRepository.__new__(MongoUmlRepository)
    repository.cache = {}
    repository._inflate(source, diagram)

    restored = repository.model(diagram)

    assert restored.id == source.id
    assert restored.classes[0].name == "Cliente"
    assert restored.classes[0].visual.x == 120
    assert repository.get_attribute(attribute_id).name == "correo"
    assert repository.get_method(method_id).parameters[0].id == parameter_id


def test_phase14_sql_foreign_keys_do_not_target_mongodb_messages() -> None:
    from app.modules.asistente_proyecto.models import AiAction, AiRecommendation

    for model in (AiAction, AiRecommendation):
        foreign_keys = model.__table__.c.source_message_id.foreign_keys
        assert not foreign_keys


def test_phase14_gate_refuses_incomplete_migrations_and_degraded_audit(monkeypatch) -> None:
    migrations = FakeCollection()
    audits = FakeCollection()
    database = FakeDatabase(
        {
            MongoCollection.MIGRATION_CHECKPOINTS.value: migrations,
            MongoCollection.OPERATIONAL_AUDITS.value: audits,
        }
    )
    session = MagicMock()
    session.scalar.return_value = 2
    session_context = MagicMock()
    session_context.__enter__.return_value = session
    session_context.__exit__.return_value = False
    monkeypatch.setattr(settings, "ai_messages_migration_required", True)
    monkeypatch.setattr(settings, "uml_versions_migration_required", True)
    monkeypatch.setattr(settings, "uml_diagrams_migration_required", True)

    with (
        patch(
            "app.core.nosql.commands.consolidate.SessionLocal",
            return_value=session_context,
        ),
        patch(
            "app.core.nosql.commands.consolidate.ReconciliationService.audit_operational",
            AsyncMock(return_value={"status": "degraded", "findings": []}),
        ),
    ):
        report = asyncio.run(ConsolidationGate(database).evaluate())

    assert report["status"] == "blocked"
    assert set(report["blockers"]) == {
        "operational_audit_degraded",
        "outbox_not_drained",
        "required_migrations_incomplete",
        "insufficient_stability_window",
    }


def test_phase14_readiness_requires_fresh_audit_and_consolidation(monkeypatch) -> None:
    checkpoints = SimpleNamespace(find_one=AsyncMock(return_value={"status": "completed"}))
    audits = SimpleNamespace(
        find_one=AsyncMock(
            return_value={
                "status": "healthy",
                "created_at": datetime.now(UTC),
            }
        )
    )
    database = {
        MongoCollection.MIGRATION_CHECKPOINTS.value: checkpoints,
        MongoCollection.OPERATIONAL_AUDITS.value: audits,
    }
    health = MongoHealth(status="available", required=True, database="case_test")
    monkeypatch.setattr(settings, "phase14_consolidation_required", True)
    monkeypatch.setattr(settings, "nosql_reconciliation_required", True)

    with (
        patch("app.main.SessionLocal", MagicMock()),
        patch.object(app.state.mongo_manager, "ping", AsyncMock(return_value=health)),
        patch.object(app.state.mongo_manager, "_database", database),
    ):
        response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json()["components"]["phase14_consolidation"]["status"] == "completed"
    assert response.json()["components"]["nosql_reconciliation"]["status"] == "healthy"
