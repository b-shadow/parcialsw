from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

CURRENT_SCHEMA_VERSION = 1


class MongoCollection(StrEnum):
    UML_DIAGRAMS = "uml_diagrams"
    UML_DIAGRAM_VERSIONS = "uml_diagram_versions"
    AI_MESSAGES = "ai_messages"
    AI_CONTEXT_SNAPSHOTS = "ai_context_snapshots"
    MIGRATION_CHECKPOINTS = "migration_checkpoints"
    PROCESSED_EVENTS = "nosql_processed_events"
    OPERATIONAL_AUDITS = "nosql_operational_audits"


MUTABLE_COLLECTIONS = frozenset(
    {
        MongoCollection.UML_DIAGRAMS,
        MongoCollection.UML_DIAGRAM_VERSIONS,
        MongoCollection.AI_MESSAGES,
        MongoCollection.AI_CONTEXT_SNAPSHOTS,
        MongoCollection.MIGRATION_CHECKPOINTS,
    }
)


class MongoDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: UUID = Field(alias="_id")
    schema_version: Literal[1] = CURRENT_SCHEMA_VERSION
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_mongo(self) -> dict[str, Any]:
        def normalize(value: Any) -> Any:
            if isinstance(value, UUID):
                return str(value)
            if isinstance(value, dict):
                return {key: normalize(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [normalize(item) for item in value]
            return value

        return normalize(self.model_dump(by_alias=True))


class UmlDiagramDocument(MongoDocument):
    project_id: UUID
    revision: int = Field(ge=0)
    content: dict[str, Any]
    content_hash: str = Field(min_length=64, max_length=64)


class UmlDiagramVersionDocument(MongoDocument):
    project_id: UUID
    diagram_id: UUID
    version_number: int = Field(ge=1)
    project_revision: int = Field(default=0, ge=0)
    snapshot_schema_version: int = Field(default=1, ge=1)
    name: str = Field(default="Version UML", min_length=1, max_length=120)
    description: str | None = None
    kind: Literal["manual", "pre_restore_backup"] = "manual"
    snapshot_size_bytes: int = Field(default=0, ge=0)
    content: dict[str, Any]
    content_hash: str = Field(min_length=64, max_length=64)
    created_by_user_id: UUID | None = None


class AiMessageDocument(MongoDocument):
    project_id: UUID
    conversation_id: UUID
    author_user_id: UUID | None = None
    role: Literal["user", "assistant", "system", "tool"]
    sequence_number: int = Field(ge=1)
    content: str = Field(min_length=1)
    correlation_id: UUID
    client_message_id: UUID | None = None
    status: Literal["pending", "streaming", "completed", "failed", "cancelled"] = "completed"
    detected_intents: list[str] = Field(default_factory=list)
    references_json: list[dict[str, Any]] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    content_hash: str = Field(min_length=64, max_length=64)


class AiContextSnapshotDocument(MongoDocument):
    project_id: UUID
    conversation_id: UUID
    until_sequence: int = Field(ge=0)
    summary: str
    context: dict[str, Any] = Field(default_factory=dict)
    content_hash: str = Field(min_length=64, max_length=64)
    expires_at: datetime | None = None


class MigrationCheckpointDocument(MongoDocument):
    migration_name: str = Field(min_length=1, max_length=160)
    status: Literal["pending", "running", "completed", "failed"]
    cursor: str | None = None
    processed_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)
    details: dict[str, Any] = Field(default_factory=dict)


class OperationalAuditDocument(MongoDocument):
    status: Literal["healthy", "degraded"]
    duration_ms: int = Field(ge=0)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    collection_reports: list[dict[str, Any]] = Field(default_factory=list)


class MongoMutation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collection: MongoCollection
    operation: Literal["upsert", "delete"]
    document_id: UUID
    document: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_mutation(self) -> MongoMutation:
        if self.collection not in MUTABLE_COLLECTIONS:
            raise ValueError("collection is not writable through the NoSQL outbox")
        if self.operation == "upsert" and self.document is None:
            raise ValueError("upsert requires a document")
        if self.operation == "delete" and self.document is not None:
            raise ValueError("delete does not accept a document")
        return self

    def normalized_document(self) -> dict[str, Any] | None:
        if self.document is None:
            return None
        document = dict(self.document)
        document_id = str(self.document_id)
        if "_id" in document and str(document["_id"]) != document_id:
            raise ValueError("document _id must match document_id")
        document["_id"] = document_id
        document.setdefault("schema_version", CURRENT_SCHEMA_VERSION)
        return document
