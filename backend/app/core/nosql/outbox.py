from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, PyMongoError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.nosql.contracts import CURRENT_SCHEMA_VERSION, MongoCollection, MongoMutation
from app.core.nosql.outbox_model import NoSqlOutboxEvent
from app.core.nosql.repositories import DOCUMENT_MODELS


class NoSqlOutboxService:
    """Adds a MongoDB mutation to the caller's existing PostgreSQL transaction."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def enqueue(
        self,
        *,
        aggregate_type: str,
        aggregate_id: UUID,
        mutation: MongoMutation,
        idempotency_key: str,
    ) -> NoSqlOutboxEvent:
        now = datetime.now(UTC)
        event = NoSqlOutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=f"mongodb.{mutation.collection.value}.{mutation.operation}",
            payload=mutation.model_dump(mode="json"),
            idempotency_key=idempotency_key,
            status="pending",
            available_at=now,
        )
        self.db.add(event)
        return event


class NoSqlOutboxDispatcher:
    LOCK_TIMEOUT = timedelta(minutes=5)

    def __init__(self, db: Session, mongo_database, *, max_attempts: int = 8) -> None:
        self.db = db
        self.mongo_database = mongo_database
        self.max_attempts = max_attempts

    def _claim(self, limit: int) -> list[NoSqlOutboxEvent]:
        now = datetime.now(UTC)
        worker = str(uuid4())
        jobs = list(
            self.db.scalars(
                select(NoSqlOutboxEvent)
                .where(
                    NoSqlOutboxEvent.available_at <= now,
                    or_(
                        NoSqlOutboxEvent.status.in_(("pending", "retry")),
                        (NoSqlOutboxEvent.status == "processing")
                        & (NoSqlOutboxEvent.locked_at < now - self.LOCK_TIMEOUT),
                    ),
                )
                .order_by(NoSqlOutboxEvent.available_at)
                .limit(max(1, min(limit, 500)))
                .with_for_update(skip_locked=True)
            )
        )
        for job in jobs:
            job.status = "processing"
            job.locked_at = now
            job.locked_by = worker
        self.db.commit()
        return jobs

    async def _already_processed(self, key: str) -> bool:
        receipt = await self.mongo_database[MongoCollection.PROCESSED_EVENTS.value].find_one(
            {"idempotency_key": key}, {"_id": 1}
        )
        return receipt is not None

    @staticmethod
    async def _patch_uml_revision(collection, existing: dict, payload: dict) -> bool:
        if int(existing.get("revision", -1)) + 1 != int(payload["revision"]):
            return False
        old_content = existing.get("content") or {}
        new_content = payload.get("content") or {}
        updates = {
            "revision": payload["revision"],
            "content_hash": payload["content_hash"],
            "updated_at": payload["updated_at"],
        }
        array_filters = []
        for key, value in new_content.items():
            if key in {"classes", "relationships"}:
                continue
            if old_content.get(key) != value:
                updates[f"content.{key}"] = value

        for collection_name, identifier in (("classes", "class"), ("relationships", "rel")):
            old_items = old_content.get(collection_name, [])
            new_items = new_content.get(collection_name, [])
            old_by_id = {str(item.get("id")): item for item in old_items}
            new_by_id = {str(item.get("id")): item for item in new_items}
            if list(old_by_id) != list(new_by_id):
                updates[f"content.{collection_name}"] = new_items
                continue
            for index, (element_id, item) in enumerate(new_by_id.items()):
                if old_by_id[element_id] == item:
                    continue
                token = f"{identifier}{index}"
                updates[f"content.{collection_name}.$[{token}]"] = item
                array_filters.append({f"{token}.id": element_id})

        kwargs = {"array_filters": array_filters} if array_filters else {}
        result = await collection.update_one(
            {"_id": payload["_id"], "revision": existing["revision"]},
            {"$set": updates},
            **kwargs,
        )
        return result.matched_count == 1

    async def _apply(self, job: NoSqlOutboxEvent) -> None:
        if await self._already_processed(job.idempotency_key):
            return
        mutation = MongoMutation.model_validate(job.payload)
        collection = self.mongo_database[mutation.collection.value]
        document_id = str(mutation.document_id)
        if mutation.operation == "delete":
            await collection.delete_one({"_id": document_id})
        else:
            document = mutation.normalized_document()
            assert document is not None
            model = DOCUMENT_MODELS[mutation.collection]
            validated = model.model_validate(document)
            payload = validated.to_mongo()
            if mutation.collection == MongoCollection.UML_DIAGRAM_VERSIONS:
                existing = await collection.find_one({"_id": document_id})
                if existing is None:
                    try:
                        await collection.insert_one(payload)
                    except DuplicateKeyError:
                        existing = await collection.find_one({"_id": document_id})
                        if existing is None:
                            raise ValueError(
                                "immutable UML version conflicts with another unique key"
                            ) from None
                if existing is not None and existing.get("content_hash") != payload.get(
                    "content_hash"
                ):
                    raise ValueError("immutable UML version already exists with different content")
                await self._record_receipt(job, mutation)
                return
            if mutation.collection == MongoCollection.UML_DIAGRAMS and {
                "id",
                "project_id",
                "name",
            }.issubset(validated.content):
                from app.modules.modelado_uml.engine.internal_model import UmlDiagramModel
                from app.modules.modelado_uml.engine.validator import validate_internal_model

                uml_model = UmlDiagramModel.model_validate(validated.content)
                if str(uml_model.id) != str(validated.id) or str(uml_model.project_id) != str(
                    validated.project_id
                ):
                    raise ValueError("UML document identity does not match its content")
                errors, _, _ = validate_internal_model(uml_model)
                if errors:
                    raise ValueError("invalid UML document references: " + "; ".join(errors))
                existing = await collection.find_one({"_id": document_id})
                if existing is not None:
                    stored_revision = int(existing.get("revision", -1))
                    incoming_revision = int(payload["revision"])
                    if stored_revision > incoming_revision:
                        await self._record_receipt(job, mutation)
                        return
                    if stored_revision == incoming_revision:
                        if existing.get("content_hash") != payload.get("content_hash"):
                            raise ValueError(
                                "UML diagram revision conflicts with different content"
                            )
                        await self._record_receipt(job, mutation)
                        return
                    if await self._patch_uml_revision(collection, existing, payload):
                        await self._record_receipt(job, mutation)
                        return
                result = await collection.replace_one(
                    {"_id": document_id, "revision": {"$lt": payload["revision"]}},
                    payload,
                    upsert=False,
                )
                if result.matched_count == 0 and existing is None:
                    try:
                        await collection.insert_one(payload)
                    except DuplicateKeyError:
                        concurrent = await collection.find_one({"_id": document_id})
                        if concurrent is None or int(concurrent.get("revision", -1)) < int(
                            payload["revision"]
                        ):
                            raise
                elif result.matched_count == 0:
                    concurrent = await collection.find_one({"_id": document_id})
                    if concurrent is None:
                        raise ValueError("UML diagram disappeared during revision update")
                    concurrent_revision = int(concurrent.get("revision", -1))
                    if concurrent_revision < int(payload["revision"]):
                        raise ValueError("UML diagram revision update was not applied")
                    if concurrent_revision == int(payload["revision"]) and concurrent.get(
                        "content_hash"
                    ) != payload.get("content_hash"):
                        raise ValueError("UML diagram revision conflicts with different content")
                await self._record_receipt(job, mutation)
                return
            updated_at = payload.get("updated_at")
            replace_filter = {"_id": document_id}
            if updated_at is not None:
                replace_filter["$or"] = [
                    {"updated_at": {"$lte": updated_at}},
                    {"updated_at": {"$exists": False}},
                ]
            result = await collection.replace_one(replace_filter, payload, upsert=False)
            if result.matched_count == 0:
                existing = await collection.find_one({"_id": document_id}, {"_id": 1})
                if existing is None:
                    try:
                        await collection.insert_one(payload)
                    except DuplicateKeyError:
                        pass

        await self._record_receipt(job, mutation)

    async def _record_receipt(self, job: NoSqlOutboxEvent, mutation: MongoMutation) -> None:
        now = datetime.now(UTC)
        receipt = {
            "_id": str(job.id),
            "schema_version": CURRENT_SCHEMA_VERSION,
            "created_at": now,
            "updated_at": now,
            "idempotency_key": job.idempotency_key,
            "event_id": str(job.id),
            "collection": mutation.collection.value,
            "operation": mutation.operation,
            "processed_at": now,
        }
        try:
            await self.mongo_database[MongoCollection.PROCESSED_EVENTS.value].insert_one(receipt)
        except DuplicateKeyError:
            pass

    async def dispatch(self, limit: int = 50) -> dict[str, int]:
        jobs = self._claim(limit)
        result = {"processed": 0, "completed": 0, "retry": 0, "dead": 0}
        for job in jobs:
            result["processed"] += 1
            try:
                await self._apply(job)
                job.status = "completed"
                job.processed_at = datetime.now(UTC)
                job.last_error = None
                result["completed"] += 1
            except (PyMongoError, ValidationError, ValueError) as exc:
                job.attempt_count += 1
                job.last_error = f"{type(exc).__name__}: {exc}"[:2000]
                if job.attempt_count >= self.max_attempts:
                    job.status = "dead"
                    result["dead"] += 1
                else:
                    job.status = "retry"
                    delay = min(3600, 2**job.attempt_count * 15) + random.randint(0, 10)
                    job.available_at = datetime.now(UTC) + timedelta(seconds=delay)
                    result["retry"] += 1
            finally:
                job.locked_at = None
                job.locked_by = None
                self.db.commit()
        return result
