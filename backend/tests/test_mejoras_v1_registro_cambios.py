"""Pruebas completas del registro de cambios en NoSQL (Redis Streams) y fallback (V1.1)."""

import json
from uuid import uuid4
import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.core.changelog.contracts import PendingChange
from app.core.changelog.service import ChangeLogService
from app.core.changelog.hooks import clear_pending_changes, flush_pending_changes, queue_change
from app.core.changelog.backfill import backfill_project
from app.core.redis.client import redis_key, set_test_client
from app.main import app
from app.modules.acceso_usuarios.models import AuditLog, User
from app.modules.proyectos_colaboracion.models import Project, ProjectMember


@pytest.fixture
def fake_redis_client():
    client = fakeredis.FakeRedis(decode_responses=True)
    set_test_client(client, None)
    yield client
    set_test_client(None, None)


def test_queue_and_flush_writes_to_streams(fake_redis_client):
    proj_id = uuid4()
    actor_id = uuid4()

    change = PendingChange(
        project_id=proj_id,
        actor_user_id=actor_id,
        source="ui",
        module="modelado_uml",
        action="CREATE_CLASS",
        entity_type="class",
        entity_id=str(uuid4()),
        metadata={"name": "Factura", "password": "secret_pwd", "token": "secret_tok"},
    )

    class DummySession:
        def __init__(self):
            self.info = {}

    db = DummySession()
    queue_change(db, change)
    assert len(db.info["change_log_pending"]) == 1

    flush_pending_changes(db)
    assert "change_log_pending" not in db.info

    p_key = redis_key("changelog", "project", str(proj_id))
    g_key = redis_key("changelog", "all")

    p_entries = fake_redis_client.xrevrange(p_key)
    g_entries = fake_redis_client.xrevrange(g_key)

    assert len(p_entries) == 1
    assert len(g_entries) == 1

    entry_id, fields = p_entries[0]
    assert fields["action"] == "CREATE_CLASS"
    assert fields["summary"] == "Creó la clase Factura"
    assert "secret_pwd" not in fields["metadata"]
    assert "secret_tok" not in fields["metadata"]


def test_rollback_discards_pending_changes(fake_redis_client):
    class DummySession:
        def __init__(self):
            self.info = {}

    db = DummySession()
    proj_id = uuid4()
    queue_change(
        db,
        PendingChange(
            project_id=proj_id,
            source="ui",
            module="modelado_uml",
            action="CREATE_CLASS",
        ),
    )

    clear_pending_changes(db)
    assert "change_log_pending" not in db.info

    flush_pending_changes(db)
    p_key = redis_key("changelog", "project", str(proj_id))
    assert len(fake_redis_client.xrevrange(p_key)) == 0


def test_pagination_and_filtering(fake_redis_client):
    proj_id = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    service = ChangeLogService()
    changes = [
        PendingChange(
            project_id=proj_id,
            actor_user_id=user_a,
            source="ui",
            module="modelado_uml",
            action="CREATE_CLASS",
            entity_type="class",
            metadata={"name": f"Clase_{i}"},
        )
        for i in range(1, 4)
    ]
    service.append_many(changes)

    # 1. Paginar limit=2
    page1 = service.list_project(proj_id, limit=2)
    assert len(page1.items) == 2
    assert page1.next_cursor is not None

    page2 = service.list_project(proj_id, before_id=page1.next_cursor, limit=2)
    assert len(page2.items) == 1

    # 2. Filtro por actor_id
    page_user_b = service.list_project(proj_id, actor_id=user_b)
    assert len(page_user_b.items) == 0


def test_fallback_when_redis_unavailable():
    set_test_client(None, None)
    service = ChangeLogService()
    proj_id = uuid4()

    page = service.list_project(proj_id, db=None)
    assert page.source == "postgres_fallback"
    assert len(page.items) == 0
