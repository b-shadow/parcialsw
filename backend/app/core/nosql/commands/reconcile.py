import argparse
import asyncio
import json
import logging
from pathlib import Path

from app.core.database.session import SessionLocal
from app.core.nosql.client import mongo_manager
from app.core.nosql.reconciliation import ReconciliationService

logger = logging.getLogger(__name__)


async def run(
    require_complete: bool,
    hash_manifest: Path | None,
    *,
    operational: bool = False,
) -> int:
    health = await mongo_manager.connect(bootstrap=True)
    if not health.available:
        print(json.dumps({"status": "unavailable", "component": "mongodb"}))
        await mongo_manager.close()
        return 1
    try:
        with SessionLocal() as db:
            expected_hashes = None
            if hash_manifest is not None:
                expected_hashes = json.loads(hash_manifest.read_text(encoding="utf-8"))
            service = ReconciliationService(db, mongo_manager.database)
            report = (
                await service.audit_operational()
                if operational
                else await service.audit_all(
                    require_complete=require_complete,
                    expected_hashes=expected_hashes,
                )
            )
    finally:
        await mongo_manager.close()
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] not in {"consistent", "healthy"}:
        logger.error("nosql_reconciliation_alert %s", json.dumps(report, sort_keys=True))
    return 0 if report["status"] in {"consistent", "healthy"} else 2


async def watch(interval_seconds: int) -> int:
    while True:
        exit_code = await run(True, None, operational=True)
        if exit_code:
            logger.error("NoSQL operational reconciliation detected drift")
        await asyncio.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit PostgreSQL and MongoDB identity drift")
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="also report PostgreSQL records that have not been migrated",
    )
    parser.add_argument(
        "--hash-manifest",
        type=Path,
        help="JSON map of collection -> document id -> expected SHA-256",
    )
    parser.add_argument("--operational", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval-seconds", type=int, default=300)
    args = parser.parse_args()
    if args.watch:
        raise SystemExit(asyncio.run(watch(max(30, args.interval_seconds))))
    raise SystemExit(
        asyncio.run(
            run(
                args.require_complete,
                args.hash_manifest,
                operational=args.operational,
            )
        )
    )


if __name__ == "__main__":
    main()
