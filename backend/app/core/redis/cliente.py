from typing import Literal

import redis
import redis.asyncio as aioredis

from app.core.config.configuracion import settings

_sync_client: redis.Redis | None = None
_async_client: aioredis.Redis | None = None
_test_sync_client: redis.Redis | None = None
_test_async_client: aioredis.Redis | None = None
_test_override: bool = False


def establecer_cliente_prueba(
    client: redis.Redis | None,
    async_client: aioredis.Redis | None = None,
) -> None:
    global _test_sync_client, _test_async_client, _test_override
    _test_sync_client = client
    _test_async_client = async_client
    _test_override = True


def obtener_redis() -> redis.Redis | None:
    global _sync_client
    if _test_override:
        return _test_sync_client
    if not settings.redis_enabled:
        return None
    if _sync_client is None:
        _sync_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=2.0,
        )
    return _sync_client


def obtener_redis_asincrono() -> aioredis.Redis | None:
    global _async_client
    if _test_override:
        return _test_async_client
    if not settings.redis_enabled:
        return None
    if _async_client is None:
        _async_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=2.0,
        )
    return _async_client


def clave_redis(*parts: str) -> str:
    cleaned = [p.strip(":") for p in parts if p]
    if not cleaned:
        return settings.redis_key_prefix
    return f"{settings.redis_key_prefix}:{':'.join(cleaned)}"


def redis_status() -> Literal["available", "unavailable", "disabled"]:
    if _test_override:
        if _test_sync_client is None:
            return "disabled"
        try:
            _test_sync_client.ping()
            return "available"
        except Exception:
            return "unavailable"

    if not settings.redis_enabled:
        return "disabled"

    try:
        client = obtener_redis()
        if client is None:
            return "disabled"
        client.ping()
        return "available"
    except Exception:
        return "unavailable"
