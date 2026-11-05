from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.core.config.configuracion import ConfiguracionAplicacion, settings
from app.core.nosql.errores import ErrorEsquemaMongo, ErrorMongoNoDisponible
from app.core.nosql.nombres_mongo import adaptar_mongo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EstadoMongo:
    status: str
    required: bool
    database: str
    detail: str | None = None

    @property
    def available(self) -> bool:
        return self.status == "available"


class GestorMongo:
    def __init__(self, config: ConfiguracionAplicacion) -> None:
        self.config = config
        self._client: AsyncMongoClient | None = None
        self._database: Any | None = None
        self._last_error: str | None = None

    @property
    def database(self) -> Any:
        if self._database is None:
            raise ErrorMongoNoDisponible("MongoDB has not been initialized")
        return adaptar_mongo(self._database)

    def _crear_cliente(self) -> AsyncMongoClient:
        return AsyncMongoClient(
            self.config.mongodb_uri,
            appname="case-inteligente-backend",
            connectTimeoutMS=self.config.mongodb_connect_timeout_ms,
            serverSelectionTimeoutMS=self.config.mongodb_server_selection_timeout_ms,
            tz_aware=True,
            retryReads=True,
            retryWrites=True,
        )

    async def connect(self, *, bootstrap: bool = True) -> EstadoMongo:
        if not self.config.mongodb_enabled:
            return self.health(status="disabled")
        if self._client is None:
            self._client = self._crear_cliente()
            self._database = self._client[self.config.mongodb_database]
        try:
            await self._client.admin.command("ping")
            if bootstrap:
                from app.core.nosql.esquema import asegurar_esquema_mongo

                await asegurar_esquema_mongo(self._database)
            self._last_error = None
            return self.health(status="available")
        except (ErrorEsquemaMongo, PyMongoError) as exc:
            self._last_error = type(exc).__name__
            logger.warning("MongoDB is unavailable: %s", self._last_error)
            return self.health(status="unavailable")

    async def ping(self) -> EstadoMongo:
        return await self.connect(bootstrap=False)

    def health(self, *, status: str | None = None) -> EstadoMongo:
        if status is None:
            status = (
                "available"
                if self._database is not None and self._last_error is None
                else "unknown"
            )
        return EstadoMongo(
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


mongo_manager = GestorMongo(settings)
