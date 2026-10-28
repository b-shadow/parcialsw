import asyncio

from app.core.nosql.client import mongo_manager


async def run() -> None:
    health = await mongo_manager.connect(bootstrap=True)
    print(f"mongodb-bootstrap status={health.status} database={health.database}")
    await mongo_manager.close()
    if not health.available:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(run())
