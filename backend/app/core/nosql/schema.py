from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.errors import CollectionInvalid, OperationFailure, PyMongoError

from app.core.nosql.contracts import MongoCollection
from app.core.nosql.errors import MongoSchemaError

UUID_PATTERN = (
    "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
HASH_PATTERN = "^[0-9a-f]{64}$"


def _base_properties() -> dict[str, Any]:
    return {
        "_id": {"bsonType": "string", "pattern": UUID_PATTERN},
        "schema_version": {"bsonType": "int", "minimum": 1},
        "created_at": {"bsonType": "date"},
        "updated_at": {"bsonType": "date"},
    }


def _validator(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "schema_version", "created_at", "updated_at", *required],
            "properties": {**_base_properties(), **properties},
            "additionalProperties": True,
        }
    }


COLLECTION_VALIDATORS: dict[MongoCollection, dict[str, Any]] = {
    MongoCollection.UML_DIAGRAMS: _validator(
        ["project_id", "revision", "content", "content_hash"],
        {
            "project_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "revision": {"bsonType": "int", "minimum": 0},
            "content": {"bsonType": "object"},
            "content_hash": {"bsonType": "string", "pattern": HASH_PATTERN},
        },
    ),
    MongoCollection.UML_DIAGRAM_VERSIONS: _validator(
        [
            "project_id",
            "diagram_id",
            "version_number",
            "project_revision",
            "snapshot_schema_version",
            "name",
            "kind",
            "snapshot_size_bytes",
            "content",
            "content_hash",
        ],
        {
            "project_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "diagram_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "version_number": {"bsonType": "int", "minimum": 1},
            "project_revision": {"bsonType": "int", "minimum": 0},
            "snapshot_schema_version": {"bsonType": "int", "minimum": 1},
            "name": {"bsonType": "string", "minLength": 1, "maxLength": 120},
            "description": {"bsonType": ["string", "null"]},
            "kind": {"enum": ["manual", "pre_restore_backup"]},
            "snapshot_size_bytes": {"bsonType": "int", "minimum": 0},
            "content": {"bsonType": "object"},
            "content_hash": {"bsonType": "string", "pattern": HASH_PATTERN},
        },
    ),
    MongoCollection.AI_MESSAGES: _validator(
        [
            "project_id",
            "conversation_id",
            "role",
            "sequence_number",
            "content",
            "correlation_id",
            "status",
            "detected_intents",
            "references_json",
            "metadata_json",
            "content_hash",
        ],
        {
            "project_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "conversation_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "role": {"enum": ["user", "assistant", "system", "tool"]},
            "sequence_number": {"bsonType": "int", "minimum": 1},
            "content": {"bsonType": "string", "minLength": 1},
            "correlation_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "status": {"enum": ["pending", "streaming", "completed", "failed", "cancelled"]},
            "detected_intents": {"bsonType": "array"},
            "references_json": {"bsonType": "array"},
            "metadata_json": {"bsonType": "object"},
            "content_hash": {"bsonType": "string", "pattern": HASH_PATTERN},
        },
    ),
    MongoCollection.AI_CONTEXT_SNAPSHOTS: _validator(
        ["project_id", "conversation_id", "until_sequence", "summary", "content_hash"],
        {
            "project_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "conversation_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "until_sequence": {"bsonType": "int", "minimum": 0},
            "summary": {"bsonType": "string"},
            "content_hash": {"bsonType": "string", "pattern": HASH_PATTERN},
            "expires_at": {"bsonType": ["date", "null"]},
        },
    ),
    MongoCollection.MIGRATION_CHECKPOINTS: _validator(
        ["migration_name", "status", "processed_count", "failed_count"],
        {
            "migration_name": {"bsonType": "string", "minLength": 1},
            "status": {"enum": ["pending", "running", "completed", "failed"]},
            "processed_count": {"bsonType": "int", "minimum": 0},
            "failed_count": {"bsonType": "int", "minimum": 0},
        },
    ),
    MongoCollection.PROCESSED_EVENTS: _validator(
        ["idempotency_key", "event_id", "collection", "operation", "processed_at"],
        {
            "idempotency_key": {"bsonType": "string", "minLength": 1},
            "event_id": {"bsonType": "string", "pattern": UUID_PATTERN},
            "collection": {"bsonType": "string"},
            "operation": {"enum": ["upsert", "delete"]},
            "processed_at": {"bsonType": "date"},
        },
    ),
    MongoCollection.OPERATIONAL_AUDITS: _validator(
        ["status", "duration_ms", "findings", "metrics", "collection_reports"],
        {
            "status": {"enum": ["healthy", "degraded"]},
            "duration_ms": {"bsonType": "int", "minimum": 0},
            "findings": {"bsonType": "array"},
            "metrics": {"bsonType": "object"},
            "collection_reports": {"bsonType": "array"},
        },
    ),
}


@dataclass(frozen=True)
class IndexDefinition:
    collection: MongoCollection
    indexes: tuple[IndexModel, ...]


INDEX_DEFINITIONS = (
    IndexDefinition(
        MongoCollection.UML_DIAGRAMS,
        (
            IndexModel([("project_id", ASCENDING)], unique=True, name="uq_uml_diagrams_project"),
            IndexModel([("updated_at", DESCENDING)], name="ix_uml_diagrams_updated"),
        ),
    ),
    IndexDefinition(
        MongoCollection.UML_DIAGRAM_VERSIONS,
        (
            IndexModel(
                [("diagram_id", ASCENDING), ("version_number", ASCENDING)],
                unique=True,
                name="uq_uml_versions_diagram_number",
            ),
            IndexModel(
                [("project_id", ASCENDING), ("created_at", DESCENDING)],
                name="ix_uml_versions_project_created",
            ),
            IndexModel(
                [("project_id", ASCENDING), ("version_number", ASCENDING)],
                unique=True,
                name="uq_uml_versions_project_number",
            ),
            IndexModel([("content_hash", ASCENDING)], name="ix_uml_versions_hash"),
        ),
    ),
    IndexDefinition(
        MongoCollection.AI_MESSAGES,
        (
            IndexModel(
                [("conversation_id", ASCENDING), ("sequence_number", ASCENDING)],
                unique=True,
                name="uq_ai_messages_conversation_sequence",
            ),
            IndexModel(
                [("project_id", ASCENDING), ("created_at", DESCENDING)],
                name="ix_ai_messages_project_created",
            ),
            IndexModel(
                [("conversation_id", ASCENDING), ("client_message_id", ASCENDING)],
                unique=True,
                partialFilterExpression={"client_message_id": {"$type": "string"}},
                name="uq_ai_messages_client_id",
            ),
        ),
    ),
    IndexDefinition(
        MongoCollection.AI_CONTEXT_SNAPSHOTS,
        (
            IndexModel(
                [("conversation_id", ASCENDING), ("until_sequence", DESCENDING)],
                unique=True,
                name="uq_ai_context_conversation_sequence",
            ),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_ai_context"),
        ),
    ),
    IndexDefinition(
        MongoCollection.MIGRATION_CHECKPOINTS,
        (
            IndexModel([("migration_name", ASCENDING)], unique=True, name="uq_migration_name"),
            IndexModel(
                [("status", ASCENDING), ("updated_at", ASCENDING)], name="ix_migration_status"
            ),
        ),
    ),
    IndexDefinition(
        MongoCollection.PROCESSED_EVENTS,
        (
            IndexModel(
                [("idempotency_key", ASCENDING)], unique=True, name="uq_processed_idempotency"
            ),
            IndexModel([("event_id", ASCENDING)], unique=True, name="uq_processed_event"),
            IndexModel([("processed_at", DESCENDING)], name="ix_processed_at"),
        ),
    ),
    IndexDefinition(
        MongoCollection.OPERATIONAL_AUDITS,
        (
            IndexModel([("created_at", DESCENDING)], name="ix_operational_audits_created"),
            IndexModel(
                [("status", ASCENDING), ("created_at", DESCENDING)],
                name="ix_operational_audits_status_created",
            ),
        ),
    ),
)


async def ensure_mongo_schema(database: Any) -> None:
    """Create or update all validators and indexes; safe to run on every startup."""
    try:
        existing = set(await database.list_collection_names())
        for collection, validator in COLLECTION_VALIDATORS.items():
            if collection.value not in existing:
                try:
                    await database.create_collection(
                        collection.value,
                        validator=validator,
                        validationLevel="strict",
                        validationAction="error",
                    )
                except CollectionInvalid:
                    pass
            await database.command(
                {
                    "collMod": collection.value,
                    "validator": validator,
                    "validationLevel": "strict",
                    "validationAction": "error",
                }
            )
        for definition in INDEX_DEFINITIONS:
            await database[definition.collection.value].create_indexes(list(definition.indexes))
    except (OperationFailure, PyMongoError) as exc:
        raise MongoSchemaError(f"MongoDB schema bootstrap failed: {type(exc).__name__}") from exc
