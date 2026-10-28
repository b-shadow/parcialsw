import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config.settings import Settings
from app.core.nosql.client import MongoHealth, MongoManager
from app.core.nosql.contracts import (
    AiMessageDocument,
    MongoCollection,
    MongoMutation,
    UmlDiagramDocument,
)
from app.core.nosql.outbox import NoSqlOutboxDispatcher, NoSqlOutboxService
from app.core.nosql.reconciliation import ReconciliationService, canonical_sha256
from app.core.nosql.schema import COLLECTION_VALIDATORS, INDEX_DEFINITIONS, ensure_mongo_schema
from app.main import app


class FakeCollection:
    def __init__(self) -> None:
        self.indexes = []

    async def create_indexes(self, indexes):
        self.indexes.extend(indexes)
        return [index.document.get("name", "index") for index in indexes]


class FakeDatabase:
    def __init__(self) -> None:
        self.names: set[str] = set()
        self.collections: dict[str, FakeCollection] = {}
        self.commands: list[dict] = []

    async def list_collection_names(self):
        return list(self.names)

    async def create_collection(self, name, **_kwargs):
        self.names.add(name)
        return self[name]

    async def command(self, command):
        self.commands.append(command)
        return {"ok": 1}

    def __getitem__(self, name):
        return self.collections.setdefault(name, FakeCollection())


class FakeCursor:
    def __init__(self, documents) -> None:
        self.documents = iter(documents)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.documents)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


def test_phase10_settings_load_mongodb_environment(monkeypatch) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.test:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "case_test")
    monkeypatch.setenv("MONGODB_REQUIRED", "true")

    configured = Settings(_env_file=None)

    assert configured.mongodb_uri == "mongodb://example.test:27017"
    assert configured.mongodb_database == "case_test"
    assert configured.mongodb_required is True


def test_phase10_document_contract_serializes_uuid_and_preserves_dates() -> None:
    now = datetime.now(UTC)
    document = UmlDiagramDocument(
        _id=uuid4(),
        project_id=uuid4(),
        revision=1,
        content={"classes": []},
        content_hash="a" * 64,
        created_at=now,
        updated_at=now,
    ).to_mongo()

    assert isinstance(document["_id"], str)
    assert isinstance(document["project_id"], str)
    assert document["created_at"] is now


def test_phase10_message_contract_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        AiMessageDocument(
            _id=uuid4(),
            project_id=uuid4(),
            conversation_id=uuid4(),
            role="user",
            sequence_number=1,
            content="",
            correlation_id=uuid4(),
            content_hash="b" * 64,
        )


def test_phase10_mutations_are_idempotent_and_restricted() -> None:
    document_id = uuid4()
    mutation = MongoMutation(
        collection=MongoCollection.UML_DIAGRAMS,
        operation="upsert",
        document_id=document_id,
        document={"revision": 1},
    )
    assert mutation.normalized_document()["_id"] == str(document_id)

    with pytest.raises(ValidationError):
        MongoMutation(
            collection=MongoCollection.PROCESSED_EVENTS,
            operation="delete",
            document_id=document_id,
        )


def test_phase10_schema_bootstrap_is_repeatable() -> None:
    database = FakeDatabase()

    asyncio.run(ensure_mongo_schema(database))
    asyncio.run(ensure_mongo_schema(database))

    assert database.names == {collection.value for collection in COLLECTION_VALIDATORS}
    assert len(database.commands) == len(COLLECTION_VALIDATORS) * 2
    assert all(database[definition.collection.value].indexes for definition in INDEX_DEFINITIONS)


def test_phase10_manager_reports_timeout_and_recovers() -> None:
    config = Settings(
        _env_file=None,
        mongodb_uri="mongodb://unavailable.invalid",
        mongodb_connect_timeout_ms=100,
        mongodb_server_selection_timeout_ms=100,
    )
    manager = MongoManager(config)
    client = MagicMock()
    client.__getitem__.return_value = FakeDatabase()
    client.admin.command = AsyncMock(
        side_effect=[ServerSelectionTimeoutError("offline"), {"ok": 1}]
    )
    client.close = AsyncMock()
    manager._create_client = MagicMock(return_value=client)

    first = asyncio.run(manager.connect(bootstrap=False))
    second = asyncio.run(manager.connect(bootstrap=False))
    asyncio.run(manager.close())

    assert first.status == "unavailable"
    assert second.status == "available"
    client.close.assert_awaited_once()


def test_phase10_outbox_enqueue_participates_in_caller_transaction() -> None:
    session = MagicMock()
    aggregate_id = uuid4()
    mutation = MongoMutation(
        collection=MongoCollection.UML_DIAGRAMS,
        operation="delete",
        document_id=aggregate_id,
    )

    event = NoSqlOutboxService(session).enqueue(
        aggregate_type="uml_diagram",
        aggregate_id=aggregate_id,
        mutation=mutation,
        idempotency_key="diagram-delete-1",
    )

    session.add.assert_called_once_with(event)
    session.commit.assert_not_called()
    assert event.payload["document_id"] == str(aggregate_id)


def test_phase10_outbox_dispatcher_applies_upsert_and_records_receipt() -> None:
    now = datetime.now(UTC)
    document_id = uuid4()
    project_id = uuid4()
    event = SimpleNamespace(
        id=uuid4(),
        payload={
            "collection": "uml_diagrams",
            "operation": "upsert",
            "document_id": str(document_id),
            "document": {
                "_id": str(document_id),
                "schema_version": 1,
                "created_at": now,
                "updated_at": now,
                "project_id": str(project_id),
                "revision": 1,
                "content": {"classes": []},
                "content_hash": "d" * 64,
            },
        },
        idempotency_key="diagram-upsert-1",
        status="processing",
        attempt_count=0,
        available_at=now,
        locked_at=now,
        locked_by="worker",
        processed_at=None,
        last_error=None,
    )
    target = SimpleNamespace(
        replace_one=AsyncMock(return_value=SimpleNamespace(matched_count=0)),
        find_one=AsyncMock(return_value=None),
        insert_one=AsyncMock(),
    )
    receipts = SimpleNamespace(find_one=AsyncMock(return_value=None), insert_one=AsyncMock())
    database = {
        MongoCollection.UML_DIAGRAMS.value: target,
        MongoCollection.PROCESSED_EVENTS.value: receipts,
    }
    session = MagicMock()
    dispatcher = NoSqlOutboxDispatcher(session, database)
    dispatcher._claim = MagicMock(return_value=[event])

    result = asyncio.run(dispatcher.dispatch())

    assert result == {"processed": 1, "completed": 1, "retry": 0, "dead": 0}
    target.replace_one.assert_awaited_once()
    replace_filter = target.replace_one.await_args.args[0]
    assert replace_filter["_id"] == str(document_id)
    assert replace_filter["$or"][0]["updated_at"]["$lte"] == now
    target.insert_one.assert_awaited_once()
    receipts.insert_one.assert_awaited_once()
    assert event.status == "completed"
    session.commit.assert_called_once()


def test_phase10_outbox_moves_permanent_failure_to_dead() -> None:
    document_id = uuid4()
    event = SimpleNamespace(
        id=uuid4(),
        payload={
            "collection": "uml_diagrams",
            "operation": "delete",
            "document_id": str(document_id),
            "document": None,
        },
        idempotency_key="diagram-delete-failing",
        status="processing",
        attempt_count=0,
        available_at=datetime.now(UTC),
        locked_at=datetime.now(UTC),
        locked_by="worker",
        processed_at=None,
        last_error=None,
    )
    target = SimpleNamespace(delete_one=AsyncMock(side_effect=ConnectionFailure("offline")))
    receipts = SimpleNamespace(find_one=AsyncMock(return_value=None))
    database = {
        MongoCollection.UML_DIAGRAMS.value: target,
        MongoCollection.PROCESSED_EVENTS.value: receipts,
    }
    session = MagicMock()
    dispatcher = NoSqlOutboxDispatcher(session, database, max_attempts=1)
    dispatcher._claim = MagicMock(return_value=[event])

    result = asyncio.run(dispatcher.dispatch())

    assert result == {"processed": 1, "completed": 0, "retry": 0, "dead": 1}
    assert event.status == "dead"
    assert "ConnectionFailure" in event.last_error


def test_phase10_reconciliation_detects_orphans_missing_and_hash_drift() -> None:
    common_id = str(uuid4())
    orphan_id = str(uuid4())
    missing_id = str(uuid4())
    collection = SimpleNamespace(
        find=MagicMock(
            return_value=FakeCursor(
                [
                    {"_id": common_id, "content_hash": "wrong"},
                    {"_id": orphan_id, "content_hash": "ok"},
                ]
            )
        )
    )
    database = {MongoCollection.UML_DIAGRAMS.value: collection}
    service = ReconciliationService(MagicMock(), database)

    audit = asyncio.run(
        service.audit_collection(
            MongoCollection.UML_DIAGRAMS,
            {common_id, missing_id},
            expected_hashes={common_id: "expected"},
            require_complete=True,
        )
    )

    assert audit.orphan_ids == (orphan_id,)
    assert audit.missing_ids == (missing_id,)
    assert audit.hash_mismatches == (common_id,)
    assert audit.consistent is False


def test_phase10_canonical_hash_is_order_independent() -> None:
    assert canonical_sha256({"a": 1, "b": [2]}) == canonical_sha256({"b": [2], "a": 1})


def test_phase10_readiness_exposes_both_datastores() -> None:
    mongo_health = MongoHealth(status="available", required=True, database="case_inteligente_nosql")
    session_factory = MagicMock()
    session_factory.return_value.__enter__.return_value.execute.return_value = None

    with (
        patch("app.main.SessionLocal", session_factory),
        patch.object(app.state.mongo_manager, "ping", AsyncMock(return_value=mongo_health)),
    ):
        response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "components": {
            "postgresql": {"status": "available", "required": True},
            "mongodb": {
                "status": "available",
                "required": True,
                "database": "case_inteligente_nosql",
            },
        },
    }
