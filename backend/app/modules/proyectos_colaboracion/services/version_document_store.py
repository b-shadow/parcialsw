from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from pymongo.errors import PyMongoError
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.nosql.client import MongoManager, mongo_manager
from app.core.nosql.contracts import (
    MongoCollection,
    MongoMutation,
    UmlDiagramVersionDocument,
)
from app.core.nosql.errors import MongoUnavailableError
from app.core.nosql.outbox import NoSqlOutboxService
from app.core.nosql.repositories import UmlDiagramVersionRepository
from app.core.nosql.sync_client import SyncMongoManager, sync_mongo_manager
from app.modules.proyectos_colaboracion.models import ProjectVersion

logger = logging.getLogger(__name__)


def _utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def version_document_from_sql(
    version: ProjectVersion, *, diagram_id: UUID
) -> UmlDiagramVersionDocument:
    return UmlDiagramVersionDocument(
        _id=version.id,
        project_id=version.project_id,
        diagram_id=diagram_id,
        version_number=version.version_number,
        project_revision=version.project_revision,
        snapshot_schema_version=version.snapshot_schema_version,
        name=version.name,
        description=version.description,
        kind=version.kind,
        snapshot_size_bytes=version.snapshot_size_bytes,
        content=dict(version.snapshot),
        content_hash=version.snapshot_hash,
        created_by_user_id=version.created_by_user_id,
        created_at=_utc(version.created_at),
        updated_at=_utc(version.updated_at),
    )


def enqueue_version_document(
    db: Session, version: ProjectVersion, *, diagram_id: UUID
) -> UmlDiagramVersionDocument:
    db.flush()
    document = version_document_from_sql(version, diagram_id=diagram_id)
    NoSqlOutboxService(db).enqueue(
        aggregate_type="uml_diagram_version",
        aggregate_id=version.id,
        mutation=MongoMutation(
            collection=MongoCollection.UML_DIAGRAM_VERSIONS,
            operation="upsert",
            document_id=version.id,
            document=document.to_mongo(),
        ),
        idempotency_key=f"uml-version:{version.id}:{document.content_hash}",
    )
    return document


def persist_version_document(
    version: ProjectVersion,
    *,
    diagram_id: UUID,
    content: dict,
    manager: SyncMongoManager = sync_mongo_manager,
) -> UmlDiagramVersionDocument:
    """Persist an immutable version without retaining its payload in SQL."""
    document = UmlDiagramVersionDocument(
        _id=version.id,
        project_id=version.project_id,
        diagram_id=diagram_id,
        version_number=version.version_number,
        project_revision=version.project_revision,
        snapshot_schema_version=version.snapshot_schema_version,
        name=version.name,
        description=version.description,
        kind=version.kind,
        snapshot_size_bytes=version.snapshot_size_bytes,
        content=content,
        content_hash=version.snapshot_hash,
        created_by_user_id=version.created_by_user_id,
        created_at=_utc(version.created_at),
        updated_at=_utc(version.updated_at),
    )
    collection = manager.database[MongoCollection.UML_DIAGRAM_VERSIONS.value]
    existing = collection.find_one({"_id": str(version.id)})
    if existing is not None:
        current = UmlDiagramVersionDocument.model_validate(existing)
        if current.content_hash != document.content_hash:
            raise ValueError("immutable UML version already exists with different content")
        return current
    collection.insert_one(document.to_mongo())
    return document


class UmlVersionDocumentStore:
    def __init__(self, manager: MongoManager = mongo_manager, *, database=None) -> None:
        self.manager = manager
        self._database = database

    @property
    def database(self):
        return self._database if self._database is not None else self.manager.database

    async def get(self, version_id: UUID) -> UmlDiagramVersionDocument | None:
        return await UmlDiagramVersionRepository(self.database).get(version_id)

    async def insert_immutable(
        self, document: UmlDiagramVersionDocument
    ) -> UmlDiagramVersionDocument:
        return await UmlDiagramVersionRepository(self.database).insert_immutable(document)

    async def safe_get(self, version_id: UUID) -> UmlDiagramVersionDocument | None:
        if not settings.uml_versions_mongodb_read_enabled:
            return None
        try:
            return await self.get(version_id)
        except (MongoUnavailableError, PyMongoError):
            logger.exception(
                "MongoDB UML version read failed", extra={"version_id": str(version_id)}
            )
            if not settings.uml_versions_sql_fallback_enabled:
                raise
            return None
