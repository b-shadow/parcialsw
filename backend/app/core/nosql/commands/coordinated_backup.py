from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import tempfile
import zipfile
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select

import app.models  # noqa: F401
from app.core.database.session import Base, SessionLocal
from app.core.nosql.client import mongo_manager
from app.core.nosql.contracts import MongoCollection
from app.core.nosql.outbox_model import NoSqlOutboxEvent
from app.modules.asistente_proyecto.models import AiConversation
from app.modules.proyectos_colaboracion.models import Project

BACKUP_SCHEMA_VERSION = 1
DATA_COLLECTIONS = tuple(
    item.value for item in MongoCollection if item not in {MongoCollection.OPERATIONAL_AUDITS}
)


def _encode(value: Any) -> Any:
    if isinstance(value, datetime):
        return {"__case_type__": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"__case_type__": "date", "value": value.isoformat()}
    if isinstance(value, UUID):
        return {"__case_type__": "uuid", "value": str(value)}
    if isinstance(value, Decimal):
        return {"__case_type__": "decimal", "value": str(value)}
    if isinstance(value, bytes):
        return {
            "__case_type__": "binary",
            "value": base64.b64encode(value).decode("ascii"),
        }
    if isinstance(value, dict):
        return {
            "__case_type__": "mapping",
            "items": [[str(key), _encode(item)] for key, item in value.items()],
        }
    if isinstance(value, (list, tuple)):
        return {"__case_type__": "list", "items": [_encode(item) for item in value]}
    return value


def _decode(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if not isinstance(value, dict):
        return value
    value_type = value.get("__case_type__")
    if value_type == "datetime":
        return datetime.fromisoformat(value["value"])
    if value_type == "date":
        return date.fromisoformat(value["value"])
    if value_type == "uuid":
        return UUID(value["value"])
    if value_type == "decimal":
        return Decimal(value["value"])
    if value_type == "binary":
        return base64.b64decode(value["value"])
    if value_type == "mapping":
        return {key: _decode(item) for key, item in value["items"]}
    if value_type == "list":
        return [_decode(item) for item in value["items"]]
    raise ValueError("invalid coordinated backup value")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(_encode(value), ensure_ascii=True, sort_keys=True).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _registry_watermark(db) -> str:
    projects = [
        (project_id, revision)
        for project_id, revision in db.execute(
            select(Project.id, Project.revision).order_by(Project.id)
        )
    ]
    conversations = [
        (conversation_id, last_sequence)
        for conversation_id, last_sequence in db.execute(
            select(AiConversation.id, AiConversation.last_message_sequence).order_by(
                AiConversation.id
            )
        )
    ]
    return _sha256(_json_bytes({"projects": projects, "conversations": conversations}))


def _assert_outbox_drained(db) -> None:
    blockers = int(
        db.scalar(
            select(func.count(NoSqlOutboxEvent.id)).where(
                NoSqlOutboxEvent.status.in_(("pending", "retry", "processing", "dead"))
            )
        )
        or 0
    )
    if blockers:
        raise RuntimeError(f"cannot back up with {blockers} unresolved Outbox events")


class CoordinatedBackupService:
    def __init__(self, database) -> None:
        self.database = database

    async def create(self, destination: Path) -> dict[str, Any]:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="case-backup-") as temp:
            root = Path(temp)
            with SessionLocal() as db:
                _assert_outbox_drained(db)
                watermark_before = _registry_watermark(db)
                sql_payload: dict[str, list[dict[str, Any]]] = {}
                for table in Base.metadata.sorted_tables:
                    rows = [dict(row) for row in db.execute(select(table)).mappings()]
                    sql_payload[table.name] = rows
                sql_bytes = _json_bytes(sql_payload)
                (root / "postgresql.json").write_bytes(sql_bytes)

            mongo_counts: dict[str, int] = {}
            mongo_hashes: dict[str, str] = {}
            for collection_name in DATA_COLLECTIONS:
                rows = [
                    item async for item in self.database[collection_name].find({}).sort("_id", 1)
                ]
                payload = _json_bytes(rows)
                filename = f"mongodb-{collection_name}.json"
                (root / filename).write_bytes(payload)
                mongo_counts[collection_name] = len(rows)
                mongo_hashes[filename] = _sha256(payload)

            with SessionLocal() as db:
                _assert_outbox_drained(db)
                watermark_after = _registry_watermark(db)
            if watermark_before != watermark_after:
                raise RuntimeError("registry changed during coordinated backup; retry")

            manifest = {
                "backup_id": str(uuid4()),
                "schema_version": BACKUP_SCHEMA_VERSION,
                "created_at": datetime.now(UTC).isoformat(),
                "registry_watermark": watermark_after,
                "postgresql": {
                    "tables": {name: len(rows) for name, rows in sql_payload.items()},
                    "sha256": _sha256(sql_bytes),
                },
                "mongodb": {"collections": mongo_counts, "sha256": mongo_hashes},
            }
            manifest_bytes = _json_bytes(manifest)
            (root / "manifest.json").write_bytes(manifest_bytes)
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for file in sorted(root.iterdir()):
                    archive.write(file, arcname=file.name)
            temporary.replace(destination)
            return manifest

    async def restore(self, source: Path, *, force: bool = False) -> dict[str, Any]:
        with zipfile.ZipFile(source, "r") as archive:
            names = set(archive.namelist())
            if "manifest.json" not in names or "postgresql.json" not in names:
                raise ValueError("backup archive is incomplete")
            manifest = _decode(json.loads(archive.read("manifest.json")))
            if manifest.get("schema_version") != BACKUP_SCHEMA_VERSION:
                raise ValueError("unsupported backup schema version")
            sql_bytes = archive.read("postgresql.json")
            if _sha256(sql_bytes) != manifest["postgresql"]["sha256"]:
                raise ValueError("PostgreSQL backup checksum mismatch")
            sql_payload = _decode(json.loads(sql_bytes))
            mongo_payload: dict[str, list[dict[str, Any]]] = {}
            for collection_name, expected_count in manifest["mongodb"]["collections"].items():
                filename = f"mongodb-{collection_name}.json"
                payload = archive.read(filename)
                if _sha256(payload) != manifest["mongodb"]["sha256"][filename]:
                    raise ValueError(f"MongoDB checksum mismatch for {collection_name}")
                rows = _decode(json.loads(payload))
                if len(rows) != expected_count:
                    raise ValueError(f"MongoDB count mismatch for {collection_name}")
                mongo_payload[collection_name] = rows

        with SessionLocal() as db:
            sql_populated = any(
                int(db.scalar(select(func.count()).select_from(table)) or 0)
                for table in Base.metadata.sorted_tables
            )
        mongo_populated = {
            collection_name
            for collection_name in mongo_payload
            if await self.database[collection_name].count_documents({})
        }
        if sql_populated and not force:
            raise RuntimeError("PostgreSQL target is not empty")
        if mongo_populated and not force:
            names = ", ".join(sorted(mongo_populated))
            raise RuntimeError(f"MongoDB target collections are not empty: {names}")

        with SessionLocal() as db:
            if force:
                for table in reversed(Base.metadata.sorted_tables):
                    db.execute(table.delete())
                db.commit()
            for table in Base.metadata.sorted_tables:
                rows = sql_payload.get(table.name, [])
                if rows:
                    db.execute(table.insert(), rows)
            db.commit()

        for collection_name, rows in mongo_payload.items():
            collection = self.database[collection_name]
            if force:
                await collection.delete_many({})
            if rows:
                await collection.insert_many(rows, ordered=True)
        return manifest


async def run(action: str, archive: Path, *, force: bool) -> int:
    health = await mongo_manager.connect(bootstrap=True)
    if not health.available:
        print(json.dumps({"status": "unavailable", "component": "mongodb"}))
        await mongo_manager.close()
        return 1
    try:
        service = CoordinatedBackupService(mongo_manager.database)
        result = (
            await service.create(archive)
            if action == "create"
            else await service.restore(archive, force=force)
        )
        print(json.dumps(_encode(result), indent=2, sort_keys=True))
        return 0
    finally:
        await mongo_manager.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Coordinated PostgreSQL and MongoDB backup")
    parser.add_argument("action", choices=("create", "restore"))
    parser.add_argument("archive", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.action, args.archive, force=args.force)))


if __name__ == "__main__":
    main()
