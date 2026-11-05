"""Ciclo de vida para workers en segundo plano (Ola 2: ConsumidorRegistroCambios)."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.changelog.consumidor import ConsumidorRegistroCambios
from app.core.config.configuracion import settings
from app.core.redis.cliente import redis_status

logger = logging.getLogger(__name__)


@asynccontextmanager
async def start_background_workers(app: FastAPI) -> AsyncIterator[None]:
    stop_event = asyncio.Event()
    worker_task: asyncio.Task | None = None

    if settings.redis_enabled and settings.ai_proactive_enabled and redis_status() == "available":
        logger.info("Iniciando ConsumidorRegistroCambios en segundo plano...")
        consumer = ConsumidorRegistroCambios()
        worker_task = asyncio.create_task(consumer.run(stop_event))

    try:
        yield
    finally:
        if worker_task:
            logger.info("Deteniendo workers en segundo plano...")
            stop_event.set()
            try:
                await asyncio.wait_for(worker_task, timeout=5.0)
            except (TimeoutError, asyncio.CancelledError):
                worker_task.cancel()
