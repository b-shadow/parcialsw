from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import func, select

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.core.nosql.client import mongo_manager
from app.core.nosql.contracts import (
    MigrationCheckpointDocument,
    MongoCollection,
)
from app.core.nosql.outbox_model import NoSqlOutboxEvent
from app.core.nosql.reconciliation import ReconciliationService
from app.core.nosql.repositories import MigrationCheckpointRepository

MIGRATION_NAME = "phase14_consolidation_v1"
CHECKPOINT_ID = uuid5(NAMESPACE_URL, f"case-inteligente:migration:{MIGRATION_NAME}")
REQUIRED_MIGRATIONS = (
    "phase11_ai_memory_v1",
    "phase12_uml_versions_v1",
    "phase13_active_uml_diagrams_v1",
)


class ConsolidationGate:
    def __init__(self, database) -> None:
        self.database = database
        self.checkpoints = MigrationCheckpointRepository(database)

    async def evaluate(self, *, minimum_healthy_audits: int = 1) -> dict:
        with SessionLocal() as db:
            audit = await ReconciliationService(db, self.database).audit_operational()
            outbox_blockers = int(
                db.scalar(
                    select(func.count(NoSqlOutboxEvent.id)).where(
                        NoSqlOutboxEvent.status.in_(("pending", "retry", "processing", "dead"))
                    )
                )
                or 0
            )

        required_migrations = (
            REQUIRED_MIGRATIONS
            if any((
                settings.ai_messages_migration_required,
                settings.uml_versions_migration_required,
                settings.uml_diagrams_migration_required,
            ))
            else ()
        )
        migration_rows = [
            item
            async for item in self.database[MongoCollection.MIGRATION_CHECKPOINTS.value].find(
                {"migration_name": {"$in": list(required_migrations)}},
                {"migration_name": 1, "status": 1},
            )
        ]
        migrations = {item["migration_name"]: item.get("status") for item in migration_rows}
        missing_migrations = [
            name for name in required_migrations if migrations.get(name) != "completed"
        ]
        since = datetime.now(UTC) - timedelta(days=7)
        healthy_audits = await self.database[
            MongoCollection.OPERATIONAL_AUDITS.value
        ].count_documents({"status": "healthy", "created_at": {"$gte": since}})
        blockers = []
        if audit["status"] != "healthy":
            blockers.append("operational_audit_degraded")
        if outbox_blockers:
            blockers.append("outbox_not_drained")
        if missing_migrations:
            blockers.append("required_migrations_incomplete")
        if healthy_audits < minimum_healthy_audits:
            blockers.append("insufficient_stability_window")

        report = {
            "status": "completed" if not blockers else "blocked",
            "migration_name": MIGRATION_NAME,
            "blockers": blockers,
            "outbox_blockers": outbox_blockers,
            "missing_migrations": missing_migrations,
            "healthy_audits_last_7_days": healthy_audits,
            "minimum_healthy_audits": minimum_healthy_audits,
            "audit": audit,
        }
        checkpoint = MigrationCheckpointDocument(
            _id=CHECKPOINT_ID,
            migration_name=MIGRATION_NAME,
            status="completed" if not blockers else "failed",
            processed_count=healthy_audits,
            failed_count=len(blockers),
            details=report,
        )
        await self.checkpoints.upsert(checkpoint)
        return report


async def run(minimum_healthy_audits: int) -> int:
    health = await mongo_manager.connect(bootstrap=True)
    if not health.available:
        print(json.dumps({"status": "unavailable", "component": "mongodb"}))
        await mongo_manager.close()
        return 1
    try:
        report = await ConsolidationGate(mongo_manager.database).evaluate(
            minimum_healthy_audits=max(1, minimum_healthy_audits)
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "completed" else 2
    finally:
        await mongo_manager.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the Phase 14 consolidation gate")
    parser.add_argument("--minimum-healthy-audits", type=int, default=3)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.minimum_healthy_audits)))


if __name__ == "__main__":
    main()
