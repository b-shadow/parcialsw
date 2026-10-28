from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import and_, func, or_, select

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.core.nosql.client import mongo_manager
from app.core.nosql.contracts import (
    MigrationCheckpointDocument,
    MongoCollection,
    UmlDiagramVersionDocument,
)
from app.core.nosql.repositories import MigrationCheckpointRepository
from app.modules.modelado_uml.models import UmlDiagram
from app.modules.proyectos_colaboracion.models import Project, ProjectVersion
from app.modules.proyectos_colaboracion.schemas.snapshot import (
    canonicalize_project_snapshot,
    snapshot_sha256,
)
from app.modules.proyectos_colaboracion.services.project_service import ProjectService
from app.modules.proyectos_colaboracion.services.version_document_store import (
    UmlVersionDocumentStore,
)

MIGRATION_NAME = "phase12_uml_versions_v1"
CHECKPOINT_ID = uuid5(NAMESPACE_URL, f"case-inteligente:migration:{MIGRATION_NAME}")


@dataclass(frozen=True)
class MigrationReport:
    status: str
    sql_versions: int
    mongo_versions: int
    migrated_versions: int
    missing_ids: tuple[str, ...]
    orphan_ids: tuple[str, ...]
    hash_mismatches: tuple[str, ...]

    @property
    def consistent(self) -> bool:
        return not (self.missing_ids or self.orphan_ids or self.hash_mismatches)


def build_version_document(
    db, version: ProjectVersion, project: Project, diagram_id: UUID
) -> UmlDiagramVersionDocument:
    parsed = ProjectService(db)._parse_snapshot(version.snapshot, project)
    canonical = canonicalize_project_snapshot(parsed)
    return UmlDiagramVersionDocument(
        _id=version.id,
        project_id=version.project_id,
        diagram_id=diagram_id,
        version_number=version.version_number,
        project_revision=version.project_revision,
        snapshot_schema_version=parsed.schema_version,
        name=version.name,
        description=version.description,
        kind=version.kind,
        snapshot_size_bytes=len(canonical),
        content=parsed.model_dump(mode="json"),
        content_hash=snapshot_sha256(parsed),
        created_by_user_id=version.created_by_user_id,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


class UmlVersionMigrator:
    def __init__(self, database, *, batch_size: int) -> None:
        self.database = database
        self.batch_size = max(10, min(batch_size, 2000))
        self.documents = UmlVersionDocumentStore(database=database)
        self.checkpoints = MigrationCheckpointRepository(database)

    async def _checkpoint(self) -> MigrationCheckpointDocument:
        current = await self.checkpoints.get_by_name(MIGRATION_NAME)
        return current or MigrationCheckpointDocument(
            _id=CHECKPOINT_ID,
            migration_name=MIGRATION_NAME,
            status="pending",
        )

    @staticmethod
    def _batch(cursor: str | None, limit: int) -> list[tuple[ProjectVersion, Project, UUID]]:
        with SessionLocal() as db:
            diagram_id = (
                select(UmlDiagram.id)
                .where(UmlDiagram.project_id == ProjectVersion.project_id)
                .order_by(UmlDiagram.created_at, UmlDiagram.id)
                .limit(1)
                .scalar_subquery()
            )
            statement = (
                select(ProjectVersion, Project, diagram_id.label("diagram_id"))
                .join(Project, Project.id == ProjectVersion.project_id)
                .order_by(ProjectVersion.created_at, ProjectVersion.id)
                .limit(limit)
            )
            if cursor:
                raw_date, raw_id = cursor.split("|", 1)
                cursor_date = datetime.fromisoformat(raw_date)
                cursor_id = UUID(raw_id)
                statement = statement.where(
                    or_(
                        ProjectVersion.created_at > cursor_date,
                        and_(
                            ProjectVersion.created_at == cursor_date,
                            ProjectVersion.id > cursor_id,
                        ),
                    )
                )
            rows = list(db.execute(statement).tuples())
            if any(row[2] is None for row in rows):
                raise ValueError("a version belongs to a project without a UML diagram")
            return rows

    async def migrate(self, *, reset_checkpoint: bool = False) -> MigrationReport:
        checkpoint = await self._checkpoint()
        if reset_checkpoint:
            checkpoint.cursor = None
            checkpoint.processed_count = 0
            checkpoint.failed_count = 0
            checkpoint.details = {}
        checkpoint.status = "running"
        checkpoint.updated_at = datetime.now(UTC)
        await self.checkpoints.upsert(checkpoint)
        migrated = 0
        try:
            while True:
                batch = self._batch(checkpoint.cursor, self.batch_size)
                if not batch:
                    break
                with SessionLocal() as db:
                    for detached_version, _, diagram_id in batch:
                        version = db.get(ProjectVersion, detached_version.id)
                        project = db.get(Project, detached_version.project_id)
                        if version is None or project is None:
                            raise ValueError("version registry disappeared during migration")
                        document = build_version_document(db, version, project, diagram_id)
                        await self.documents.insert_immutable(document)
                migrated += len(batch)
                last = batch[-1][0]
                checkpoint.cursor = f"{last.created_at.isoformat()}|{last.id}"
                checkpoint.processed_count += len(batch)
                checkpoint.updated_at = datetime.now(UTC)
                checkpoint.details = {"last_batch_size": len(batch)}
                await self.checkpoints.upsert(checkpoint)

            report = await self.verify(migrated_versions=migrated)
            checkpoint.status = "completed" if report.consistent else "failed"
            checkpoint.failed_count = len(
                report.missing_ids + report.orphan_ids + report.hash_mismatches
            )
            checkpoint.details = asdict(report)
            checkpoint.updated_at = datetime.now(UTC)
            await self.checkpoints.upsert(checkpoint)
            return report
        except Exception as exc:
            checkpoint.status = "failed"
            checkpoint.failed_count += 1
            checkpoint.details = {"error": type(exc).__name__}
            checkpoint.updated_at = datetime.now(UTC)
            await self.checkpoints.upsert(checkpoint)
            raise

    async def verify(self, *, migrated_versions: int = 0) -> MigrationReport:
        collection = self.database[MongoCollection.UML_DIAGRAM_VERSIONS.value]
        missing: list[str] = []
        mismatches: list[str] = []
        cursor: str | None = None
        while True:
            batch = self._batch(cursor, self.batch_size)
            if not batch:
                break
            ids = [str(item[0].id) for item in batch]
            stored = {
                str(row["_id"]): row.get("content_hash")
                async for row in collection.find(
                    {"_id": {"$in": ids}}, {"_id": 1, "content_hash": 1}
                )
            }
            with SessionLocal() as db:
                for detached_version, _, diagram_id in batch:
                    version = db.get(ProjectVersion, detached_version.id)
                    project = db.get(Project, detached_version.project_id)
                    if version is None or project is None:
                        continue
                    expected = build_version_document(db, version, project, diagram_id)
                    key = str(version.id)
                    if key not in stored and len(missing) < 1000:
                        missing.append(key)
                    elif stored.get(key) != expected.content_hash and len(mismatches) < 1000:
                        mismatches.append(key)
            last = batch[-1][0]
            cursor = f"{last.created_at.isoformat()}|{last.id}"

        orphans: list[str] = []
        async for row in collection.find({}, {"_id": 1}).batch_size(self.batch_size):
            try:
                version_id = UUID(str(row["_id"]))
            except ValueError:
                version_id = None
            with SessionLocal() as db:
                exists = version_id is not None and db.get(ProjectVersion, version_id) is not None
            if not exists and len(orphans) < 1000:
                orphans.append(str(row["_id"]))

        with SessionLocal() as db:
            sql_count = int(db.scalar(select(func.count(ProjectVersion.id))) or 0)
        mongo_count = await collection.count_documents({})
        consistent = not missing and not orphans and not mismatches
        return MigrationReport(
            status="consistent" if consistent else "drift",
            sql_versions=sql_count,
            mongo_versions=mongo_count,
            migrated_versions=migrated_versions,
            missing_ids=tuple(sorted(missing)),
            orphan_ids=tuple(sorted(orphans)),
            hash_mismatches=tuple(sorted(mismatches)),
        )


async def run(*, verify_only: bool, reset_checkpoint: bool, batch_size: int) -> int:
    health = await mongo_manager.connect(bootstrap=True)
    if not health.available:
        await mongo_manager.close()
        print(json.dumps({"status": "unavailable", "component": "mongodb"}))
        return 1
    try:
        migrator = UmlVersionMigrator(mongo_manager.database, batch_size=batch_size)
        report = (
            await migrator.verify()
            if verify_only
            else await migrator.migrate(reset_checkpoint=reset_checkpoint)
        )
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
        return 0 if report.consistent else 2
    finally:
        await mongo_manager.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate immutable UML versions to MongoDB")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument(
        "--batch-size", type=int, default=settings.uml_versions_migration_batch_size
    )
    args = parser.parse_args()
    raise SystemExit(
        asyncio.run(
            run(
                verify_only=args.verify_only,
                reset_checkpoint=args.reset_checkpoint,
                batch_size=args.batch_size,
            )
        )
    )


if __name__ == "__main__":
    main()
