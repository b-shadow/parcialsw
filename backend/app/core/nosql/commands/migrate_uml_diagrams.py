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
from app.core.nosql.contracts import MigrationCheckpointDocument, MongoCollection
from app.core.nosql.repositories import MigrationCheckpointRepository
from app.modules.modelado_uml.models import UmlDiagram
from app.modules.modelado_uml.services.active_diagram_store import diagram_document_from_sql
from app.modules.proyectos_colaboracion.models import Project

MIGRATION_NAME = "phase13_active_uml_diagrams_v1"
CHECKPOINT_ID = uuid5(NAMESPACE_URL, f"case-inteligente:migration:{MIGRATION_NAME}")


@dataclass(frozen=True)
class MigrationReport:
    status: str
    sql_diagrams: int
    mongo_diagrams: int
    migrated_diagrams: int
    missing_ids: tuple[str, ...]
    orphan_ids: tuple[str, ...]
    hash_mismatches: tuple[str, ...]
    revision_mismatches: tuple[str, ...]

    @property
    def consistent(self) -> bool:
        return not (
            self.missing_ids or self.orphan_ids or self.hash_mismatches or self.revision_mismatches
        )


class ActiveUmlDiagramMigrator:
    def __init__(self, database, *, batch_size: int) -> None:
        self.database = database
        self.batch_size = max(10, min(batch_size, 1000))
        self.checkpoints = MigrationCheckpointRepository(database)

    async def _checkpoint(self) -> MigrationCheckpointDocument:
        current = await self.checkpoints.get_by_name(MIGRATION_NAME)
        return current or MigrationCheckpointDocument(
            _id=CHECKPOINT_ID, migration_name=MIGRATION_NAME, status="pending"
        )

    @staticmethod
    def _batch(cursor: str | None, limit: int) -> list[tuple[UUID, datetime]]:
        with SessionLocal() as db:
            statement = (
                select(UmlDiagram.id, UmlDiagram.updated_at)
                .order_by(UmlDiagram.updated_at, UmlDiagram.id)
                .limit(limit)
            )
            if cursor:
                raw_date, raw_id = cursor.split("|", 1)
                cursor_date, cursor_id = datetime.fromisoformat(raw_date), UUID(raw_id)
                statement = statement.where(
                    or_(
                        UmlDiagram.updated_at > cursor_date,
                        and_(UmlDiagram.updated_at == cursor_date, UmlDiagram.id > cursor_id),
                    )
                )
            return list(db.execute(statement).tuples())

    @staticmethod
    def _document(diagram_id: UUID):
        with SessionLocal() as db:
            diagram = db.get(UmlDiagram, diagram_id)
            if diagram is None:
                return None
            revision = db.scalar(select(Project.revision).where(Project.id == diagram.project_id))
            if revision is None:
                raise ValueError("diagram belongs to a missing project")
            return diagram_document_from_sql(db, diagram, revision=revision)

    async def _store(self, document) -> None:
        collection = self.database[MongoCollection.UML_DIAGRAMS.value]
        payload = document.to_mongo()
        current = await collection.find_one({"_id": payload["_id"]})
        if current is not None and int(current.get("revision", -1)) > document.revision:
            return
        if current is not None and int(current.get("revision", -1)) == document.revision:
            if current.get("content_hash") == document.content_hash:
                return
            raise ValueError(
                f"diagram {document.id} has conflicting content at revision {document.revision}"
            )
        await collection.replace_one(
            {
                "_id": payload["_id"],
                "$or": [
                    {"revision": {"$lt": document.revision}},
                    {"revision": {"$exists": False}},
                ],
            },
            payload,
            upsert=current is None,
        )

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
                for diagram_id, _ in batch:
                    document = self._document(diagram_id)
                    if document is not None:
                        await self._store(document)
                migrated += len(batch)
                last_id, last_date = batch[-1]
                checkpoint.cursor = f"{last_date.isoformat()}|{last_id}"
                checkpoint.processed_count += len(batch)
                checkpoint.details = {"last_batch_size": len(batch)}
                checkpoint.updated_at = datetime.now(UTC)
                await self.checkpoints.upsert(checkpoint)
            report = await self.verify(migrated_diagrams=migrated)
            checkpoint.status = "completed" if report.consistent else "failed"
            checkpoint.failed_count = len(
                report.missing_ids
                + report.orphan_ids
                + report.hash_mismatches
                + report.revision_mismatches
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

    async def verify(self, *, migrated_diagrams: int = 0) -> MigrationReport:
        collection = self.database[MongoCollection.UML_DIAGRAMS.value]
        missing: list[str] = []
        hashes: list[str] = []
        revisions: list[str] = []
        cursor: str | None = None
        while True:
            batch = self._batch(cursor, self.batch_size)
            if not batch:
                break
            ids = [str(item[0]) for item in batch]
            stored = {
                str(row["_id"]): row
                async for row in collection.find(
                    {"_id": {"$in": ids}}, {"_id": 1, "content_hash": 1, "revision": 1}
                )
            }
            for diagram_id, _ in batch:
                expected = self._document(diagram_id)
                if expected is None:
                    continue
                key = str(diagram_id)
                actual = stored.get(key)
                if actual is None and len(missing) < 1000:
                    missing.append(key)
                elif actual is not None:
                    if actual.get("content_hash") != expected.content_hash and len(hashes) < 1000:
                        hashes.append(key)
                    if actual.get("revision") != expected.revision and len(revisions) < 1000:
                        revisions.append(key)
            last_id, last_date = batch[-1]
            cursor = f"{last_date.isoformat()}|{last_id}"

        orphans: list[str] = []
        async for row in collection.find({}, {"_id": 1}).batch_size(self.batch_size):
            try:
                diagram_id = UUID(str(row["_id"]))
            except ValueError:
                diagram_id = None
            with SessionLocal() as db:
                exists = diagram_id is not None and db.get(UmlDiagram, diagram_id) is not None
            if not exists and len(orphans) < 1000:
                orphans.append(str(row["_id"]))
        with SessionLocal() as db:
            sql_count = int(db.scalar(select(func.count(UmlDiagram.id))) or 0)
        mongo_count = await collection.count_documents({})
        consistent = not missing and not orphans and not hashes and not revisions
        return MigrationReport(
            status="consistent" if consistent else "drift",
            sql_diagrams=sql_count,
            mongo_diagrams=mongo_count,
            migrated_diagrams=migrated_diagrams,
            missing_ids=tuple(sorted(missing)),
            orphan_ids=tuple(sorted(orphans)),
            hash_mismatches=tuple(sorted(hashes)),
            revision_mismatches=tuple(sorted(revisions)),
        )


async def run(*, verify_only: bool, reset_checkpoint: bool, batch_size: int) -> int:
    health = await mongo_manager.connect(bootstrap=True)
    if not health.available:
        await mongo_manager.close()
        print(json.dumps({"status": "unavailable", "component": "mongodb"}))
        return 1
    try:
        migrator = ActiveUmlDiagramMigrator(mongo_manager.database, batch_size=batch_size)
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
    parser = argparse.ArgumentParser(description="Migrate active UML diagrams to MongoDB")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument(
        "--batch-size", type=int, default=settings.uml_diagrams_migration_batch_size
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
