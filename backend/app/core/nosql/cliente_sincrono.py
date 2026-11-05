from __future__ import annotations

from typing import Any

from pymongo import MongoClient

from app.core.config.configuracion import ConfiguracionAplicacion, settings
from app.core.nosql.cliente import mongo_manager
from app.core.nosql.errores import ErrorMongoNoDisponible
from app.core.nosql.nombres_mongo import adaptar_mongo


class GestorMongoSincrono:
    """Lazy synchronous client for FastAPI thread-pool services."""

    def __init__(self, config: ConfiguracionAplicacion = settings) -> None:
        self.config = config
        self._client: MongoClient | None = None
        self._database: Any | None = None

    @property
    def database(self):
        if not self.config.mongodb_enabled:
            raise ErrorMongoNoDisponible("MongoDB is disabled")
        if mongo_manager.health().status != "available":
            raise ErrorMongoNoDisponible("MongoDB is not available")
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
        return adaptar_mongo(self._database)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._database = None


sync_mongo_manager = GestorMongoSincrono()
