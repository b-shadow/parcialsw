import asyncio
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

from app.core.config.settings import settings


class ProjectAiRateLimiter:
    """Limite local por usuario/proyecto para el despliegue de instancia unica."""

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._active: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str) -> None:
        async with self._lock:
            now = time.monotonic()
            requests = self._requests[key]
            while requests and requests[0] <= now - 60:
                requests.popleft()
            if len(requests) >= settings.ai_messages_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Limite de consultas de IA alcanzado; espera un momento",
                )
            if self._active[key] >= settings.ai_max_concurrent_per_user_project:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una consulta de IA en proceso para este usuario",
                )
            requests.append(now)
            self._active[key] += 1

    async def release(self, key: str) -> None:
        async with self._lock:
            self._active[key] = max(0, self._active[key] - 1)
            if self._active[key] == 0:
                self._active.pop(key, None)


project_ai_rate_limiter = ProjectAiRateLimiter()
