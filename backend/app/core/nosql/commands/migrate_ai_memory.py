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
from app.modules.asistente_proyecto.models import AiConversation, AiMessage
from app.modules.asistente_proyecto.services.conversation_document_store import (
    ConversationDocumentStore,
    context_snapshot_document,
    message_content_hash,
    message_document_from_sql,
)

MIGRATION_NAME = "phase11_ai_memory_v1"
CHECKPOINT_ID = uuid5(NAMESPACE_URL, f"case-inteligente:migration:{MIGRATION_NAME}")


def _summary_context(raw_summary: str) -> dict:
    try:
        parsed = json.loads(raw_summary)
        return parsed if isinstance(parsed, dict) else {"legacy_summary": raw_summary}
    except (TypeError, ValueError):
        return {"legacy_summary": raw_summary}


@dataclass(frozen=True)
class MigrationReport:
    status: str
    sql_messages: int
    mongo_messages: int
    migrated_messages: int
    migrated_contexts: int
    sql_contexts: int
    mongo_contexts: int
    missing_ids: tuple[str, ...]
    orphan_ids: tuple[str, ...]
    hash_mismatches: tuple[str, ...]
    context_mismatches: tuple[str, ...]

    @property
    def consistent(self) -> bool:
        return not (
            self.missing_ids or self.orphan_ids or self.hash_mismatches or self.context_mismatches
        )


class AiMemoryMigrator:
    def __init__(self, database, *, batch_size: int) -> None:
        self.database = database
        self.batch_size = max(10, min(batch_size, 2000))
        self.documents = ConversationDocumentStore(database=database)
        self.checkpoints = MigrationCheckpointRepository(database)

    async def _checkpoint(self) -> MigrationCheckpointDocument:
        current = await self.checkpoints.get_by_name(MIGRATION_NAME)
        if current is not None:
            return current
        return MigrationCheckpointDocument(
            _id=CHECKPOINT_ID,
            migration_name=MIGRATION_NAME,
            status="pending",
        )

    async def migrate(self, *, reset_checkpoint: bool = False) -> MigrationReport:
        checkpoint = await self._checkpoint()
        if reset_checkpoint:
            checkpoint.status = "pending"
            checkpoint.cursor = None
            checkpoint.processed_count = 0
            checkpoint.failed_count = 0
            checkpoint.details = {}
        checkpoint.status = "running"
        checkpoint.updated_at = datetime.now(UTC)
        await self.checkpoints.upsert(checkpoint)
        migrated = 0
        contexts = 0
        try:
            while True:
                with SessionLocal() as db:
                    statement = (
                        select(AiMessage)
                        .order_by(AiMessage.created_at, AiMessage.id)
                        .limit(self.batch_size)
                    )
                    if checkpoint.cursor:
                        cursor_date_raw, cursor_id_raw = checkpoint.cursor.split("|", 1)
                        cursor_date = datetime.fromisoformat(cursor_date_raw)
                        cursor_id = UUID(cursor_id_raw)
                        statement = statement.where(
                            or_(
                                AiMessage.created_at > cursor_date,
                                and_(
                                    AiMessage.created_at == cursor_date,
                                    AiMessage.id > cursor_id,
                                ),
                            )
                        )
                    messages = list(db.scalars(statement))
                    for message in messages:
                        await self.documents.upsert_message(message_document_from_sql(message))
                if not messages:
                    break
                migrated += len(messages)
                checkpoint.cursor = f"{messages[-1].created_at.isoformat()}|{messages[-1].id}"
                checkpoint.processed_count += len(messages)
                checkpoint.updated_at = datetime.now(UTC)
                checkpoint.details = {"last_batch_size": len(messages)}
                await self.checkpoints.upsert(checkpoint)

            with SessionLocal() as db:
                conversations = list(
                    db.scalars(
                        select(AiConversation).where(
                            AiConversation.summary.is_not(None),
                            AiConversation.summary_until_sequence > 0,
                        )
                    )
                )
                for conversation in conversations:
                    raw_summary = conversation.summary or ""
                    document = context_snapshot_document(
                        conversation,
                        summary=raw_summary,
                        context=_summary_context(raw_summary),
                        until_sequence=conversation.summary_until_sequence,
                    )
                    await self.documents.upsert_context(document)
                    contexts += 1

            report = await self.verify(migrated_messages=migrated, migrated_contexts=contexts)
            checkpoint.status = "completed" if report.consistent else "failed"
            checkpoint.failed_count = len(
                report.missing_ids
                + report.orphan_ids
                + report.hash_mismatches
                + report.context_mismatches
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

    async def verify(
        self, *, migrated_messages: int = 0, migrated_contexts: int = 0
    ) -> MigrationReport:
        with SessionLocal() as db:
            sql_count = int(db.scalar(select(func.count(AiMessage.id))) or 0)
            sql_contexts = list(
                db.scalars(
                    select(AiConversation).where(
                        AiConversation.summary.is_not(None),
                        AiConversation.summary_until_sequence > 0,
                    )
                )
            )
        mongo_collection = self.database[MongoCollection.AI_MESSAGES.value]
        mongo_count = await mongo_collection.count_documents({})
        missing_items: list[str] = []
        mismatch_items: list[str] = []
        cursor_date: datetime | None = None
        cursor_id: UUID | None = None
        while True:
            with SessionLocal() as db:
                statement = (
                    select(AiMessage)
                    .order_by(AiMessage.created_at, AiMessage.id)
                    .limit(self.batch_size)
                )
                if cursor_date is not None and cursor_id is not None:
                    statement = statement.where(
                        or_(
                            AiMessage.created_at > cursor_date,
                            and_(
                                AiMessage.created_at == cursor_date,
                                AiMessage.id > cursor_id,
                            ),
                        )
                    )
                batch = list(db.scalars(statement))
            if not batch:
                break
            identifiers = [str(item.id) for item in batch]
            mongo_rows = [
                row
                async for row in mongo_collection.find(
                    {"_id": {"$in": identifiers}}, {"_id": 1, "content_hash": 1}
                )
            ]
            hashes = {str(item["_id"]): item.get("content_hash") for item in mongo_rows}
            for item in batch:
                key = str(item.id)
                if key not in hashes:
                    if len(missing_items) < 1000:
                        missing_items.append(key)
                elif hashes[key] != message_content_hash(item) and len(mismatch_items) < 1000:
                    mismatch_items.append(key)
            cursor_date = batch[-1].created_at
            cursor_id = batch[-1].id

        orphan_items: list[str] = []
        mongo_id_batch: list[str] = []

        async def detect_orphans(identifiers: list[str]) -> None:
            valid_ids: list[UUID] = []
            for value in identifiers:
                try:
                    valid_ids.append(UUID(value))
                except ValueError:
                    pass
            with SessionLocal() as db:
                existing = {
                    str(value)
                    for value in db.scalars(select(AiMessage.id).where(AiMessage.id.in_(valid_ids)))
                }
            for value in identifiers:
                if value not in existing and len(orphan_items) < 1000:
                    orphan_items.append(value)

        mongo_cursor = mongo_collection.find({}, {"_id": 1}).batch_size(self.batch_size)
        async for row in mongo_cursor:
            mongo_id_batch.append(str(row["_id"]))
            if len(mongo_id_batch) >= self.batch_size:
                await detect_orphans(mongo_id_batch)
                mongo_id_batch = []
        if mongo_id_batch:
            await detect_orphans(mongo_id_batch)

        missing = tuple(sorted(missing_items))
        orphans = tuple(sorted(orphan_items))
        mismatches = tuple(sorted(mismatch_items))
        context_collection = self.database[MongoCollection.AI_CONTEXT_SNAPSHOTS.value]
        context_mismatches = []
        for conversation in sql_contexts:
            expected = context_snapshot_document(
                conversation,
                summary=conversation.summary or "",
                context=_summary_context(conversation.summary or ""),
                until_sequence=conversation.summary_until_sequence,
            )
            stored = await context_collection.find_one({"_id": str(expected.id)})
            if stored is None or stored.get("content_hash") != expected.content_hash:
                context_mismatches.append(str(conversation.id))
        mongo_context_count = await context_collection.count_documents({})
        consistent = not missing and not orphans and not mismatches and not context_mismatches
        return MigrationReport(
            status="consistent" if consistent else "drift",
            sql_messages=sql_count,
            mongo_messages=mongo_count,
            migrated_messages=migrated_messages,
            migrated_contexts=migrated_contexts,
            sql_contexts=len(sql_contexts),
            mongo_contexts=mongo_context_count,
            missing_ids=missing,
            orphan_ids=orphans,
            hash_mismatches=mismatches,
            context_mismatches=tuple(sorted(context_mismatches)),
        )


async def run(*, verify_only: bool, reset_checkpoint: bool, batch_size: int) -> int:
    health = await mongo_manager.connect(bootstrap=True)
    if not health.available:
        await mongo_manager.close()
        print(json.dumps({"status": "unavailable", "component": "mongodb"}))
        return 1
    try:
        migrator = AiMemoryMigrator(mongo_manager.database, batch_size=batch_size)
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
    parser = argparse.ArgumentParser(description="Migrate AI messages and memory to MongoDB")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument("--batch-size", type=int, default=settings.ai_messages_migration_batch_size)
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
