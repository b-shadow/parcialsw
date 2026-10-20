from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def start_background_workers(app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida para workers en segundo plano (Ola 0: contexto vacío)."""
    yield
