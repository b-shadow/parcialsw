import argparse
import asyncio

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.core.nosql.client import mongo_manager
from app.core.nosql.outbox import NoSqlOutboxDispatcher


async def dispatch_once() -> dict[str, int]:
    with SessionLocal() as db:
        return await NoSqlOutboxDispatcher(
            db,
            mongo_manager.database,
            max_attempts=settings.mongodb_outbox_max_attempts,
        ).dispatch(settings.mongodb_outbox_batch_size)


async def run(*, watch: bool, drain: bool, poll_seconds: float) -> None:
    health = await mongo_manager.connect(bootstrap=True)
    if not health.available:
        await mongo_manager.close()
        raise SystemExit("MongoDB unavailable; outbox was not modified")
    try:
        while True:
            result = await dispatch_once()
            print(
                "nosql-outbox "
                f"processed={result['processed']} completed={result['completed']} "
                f"retry={result['retry']} dead={result['dead']}",
                flush=True,
            )
            if not watch:
                if not drain or result["processed"] == 0:
                    break
                if result["retry"] or result["dead"]:
                    raise SystemExit("NoSQL Outbox drain stopped with unresolved events")
            await asyncio.sleep(max(0.5, poll_seconds))
    finally:
        await mongo_manager.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch PostgreSQL NoSQL outbox events")
    parser.add_argument("--watch", action="store_true", help="continuously poll for events")
    parser.add_argument("--drain", action="store_true", help="dispatch until no jobs remain")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()
    asyncio.run(run(watch=args.watch, drain=args.drain, poll_seconds=args.poll_seconds))


if __name__ == "__main__":
    main()
