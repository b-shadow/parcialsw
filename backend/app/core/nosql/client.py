from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.core.config.settings import Settings, settings
from app.core.nosql.errors import MongoSchemaError, MongoUnavailableError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MongoHealth:
    status: str
    required: bool
    database: str
    detail: str | None = None

    @property
    def available(self) -> bool:
        return self.status == "available"


class MongoManager:
    def __init__(self, config: Settings) -> None:
        self.config = config
        self._client: AsyncMongoClient | None = None
        self._database: Any | None = None
        self._last_error: str | None = None

    @property
    def database(self) -> Any:
        if self._database is None:
            raise MongoUnavailableError("MongoDB has not been initialized")
        return self._database

    def _create_client(self) -> AsyncMongoClient:
        return AsyncMongoClient(
            self.config.mongodb_uri,
            appname="case-inteligente-backend",
            connectTimeoutMS=self.config.mongodb_connect_timeout_ms,
            serverSelectionTimeoutMS=self.config.mongodb_server_selection_timeout_ms,
            tz_aware=True,
            retryReads=True,
            retryWrites=True,
        )

    async def connect(self, *, bootstrap: bool = True) -> MongoHealth:
        if not self.config.mongodb_enabled:
            return self.health(status="disabled")
        if self._client is None:
            self._client = self._create_client()
            self._database = self._client[self.config.mongodb_database]
        try:
            await self._client.admin.command("ping")
            if bootstrap:
                from app.core.nosql.schema import ensure_mongo_schema

                await ensure_mongo_schema(self.database)
            self._last_error = None
            return self.health(status="available")
        except (MongoSchemaError, PyMongoError) as exc:
            self._last_error = type(exc).__name__
            logger.warning("MongoDB is unavailable: %s", self._last_error)
            return self.health(status="unavailable")

    async def ping(self) -> MongoHealth:
        return await self.connect(bootstrap=False)

    def health(self, *, status: str | None = None) -> MongoHealth:
        if status is None:
            status = (
                "available"
                if self._database is not None and self._last_error is None
                else "unknown"
            )
        return MongoHealth(
            status=status,
            required=self.config.mongodb_required,
            database=self.config.mongodb_database,
            detail=self._last_error,
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
        self._client = None
        self._database = None
        self._last_error = None


mongo_manager = MongoManager(settings)
