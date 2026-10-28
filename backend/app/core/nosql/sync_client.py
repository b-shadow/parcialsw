from __future__ import annotations

from typing import Any

from pymongo import MongoClient

from app.core.config.settings import Settings, settings
from app.core.nosql.client import mongo_manager
from app.core.nosql.errors import MongoUnavailableError


class SyncMongoManager:
    """Lazy synchronous client for FastAPI thread-pool services."""

    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self._client: MongoClient | None = None
        self._database: Any | None = None

    @property
    def database(self):
        if not self.config.mongodb_enabled:
            raise MongoUnavailableError("MongoDB is disabled")
        if mongo_manager.health().status != "available":
            raise MongoUnavailableError("MongoDB is not available")
        if self._client is None:
            self._client = MongoClient(
                self.config.mongodb_uri,
                appname="case-inteligente-backend-sync",
                connectTimeoutMS=self.config.mongodb_connect_timeout_ms,
                serverSelectionTimeoutMS=self.config.mongodb_server_selection_timeout_ms,
                tz_aware=True,
                retryReads=True,
                retryWrites=True,
            )
            self._database = self._client[self.config.mongodb_database]
        return self._database

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._database = None


sync_mongo_manager = SyncMongoManager()
