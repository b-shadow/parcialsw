"""Pruebas de Redis opcional y salud (V0.2)."""

from unittest.mock import MagicMock, patch
import fakeredis
from fastapi.testclient import TestClient
import redis.exceptions

from app.core.config.settings import settings
from app.core.redis.client import (
    get_redis,
    redis_key,
    redis_status,
    set_test_client,
)
from app.main import app


def test_redis_disabled_by_default():
    set_test_client(None, None)
    assert not settings.redis_enabled
    assert get_redis() is None
    assert redis_status() == "disabled"


def test_redis_with_fakeredis():
    fake_sync = fakeredis.FakeRedis(decode_responses=True)
    set_test_client(fake_sync, None)
    try:
        assert redis_status() == "available"
        assert redis_key("lock", "x") == "case:lock:x"
        assert redis_key("changelog", "project", "123") == "case:changelog:project:123"
    finally:
        set_test_client(None, None)


def test_redis_connection_error_returns_unavailable():
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.exceptions.ConnectionError("Connection refused")
    set_test_client(mock_client, None)
    try:
        status = redis_status()
        assert status == "unavailable"
    finally:
        set_test_client(None, None)


def test_ready_endpoint_with_redis_disabled():
    set_test_client(None, None)
    with patch("app.main.SessionLocal") as session_factory:
        session_factory.return_value.__enter__.return_value.execute.return_value = True
        client = TestClient(app)
        response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "available"
    assert data["redis"] == "disabled"
