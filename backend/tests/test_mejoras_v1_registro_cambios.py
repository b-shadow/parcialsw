"""Pruebas completas del registro de cambios en NoSQL (Redis Streams) y fallback (V1.1)."""

from uuid import uuid4

import fakeredis
import pytest

from app.core.changelog.contratos import CambioPendiente
from app.core.changelog.ganchos import (
    encolar_cambio,
    limpiar_cambios_pendientes,
    vaciar_cambios_pendientes,
)
from app.core.changelog.servicio import ServicioRegistroCambios
from app.core.redis.cliente import clave_redis, establecer_cliente_prueba


@pytest.fixture
def fake_redis_client():
    client = fakeredis.FakeRedis(decode_responses=True)
    establecer_cliente_prueba(client, None)
    yield client
    establecer_cliente_prueba(None, None)


def test_queue_and_flush_writes_to_streams(fake_redis_client):
    proj_id = uuid4()
    actor_id = uuid4()

    change = CambioPendiente(
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
    encolar_cambio(db, change)
    assert len(db.info["change_log_pending"]) == 1

    vaciar_cambios_pendientes(db)
    assert "change_log_pending" not in db.info

    p_key = clave_redis("changelog", "project", str(proj_id))
    g_key = clave_redis("changelog", "all")

    p_entries = fake_redis_client.xrevrange(p_key)
    g_entries = fake_redis_client.xrevrange(g_key)

    assert len(p_entries) == 1
    assert len(g_entries) == 1

    _entry_id, fields = p_entries[0]
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
    encolar_cambio(
        db,
        CambioPendiente(
            project_id=proj_id,
            source="ui",
            module="modelado_uml",
            action="CREATE_CLASS",
        ),
    )

    limpiar_cambios_pendientes(db)
    assert "change_log_pending" not in db.info

    vaciar_cambios_pendientes(db)
    p_key = clave_redis("changelog", "project", str(proj_id))
    assert len(fake_redis_client.xrevrange(p_key)) == 0


def test_pagination_and_filtering(fake_redis_client):
    proj_id = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    service = ServicioRegistroCambios()
    changes = [
        CambioPendiente(
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
    page1 = service.listar_proyecto(proj_id, limit=2)
    assert len(page1.items) == 2
    assert page1.next_cursor is not None

    page2 = service.listar_proyecto(proj_id, before_id=page1.next_cursor, limit=2)
    assert len(page2.items) == 1

    # 2. Filtro por actor_id
    page_user_b = service.listar_proyecto(proj_id, actor_id=user_b)
    assert len(page_user_b.items) == 0


def test_fallback_when_redis_unavailable():
    establecer_cliente_prueba(None, None)
    service = ServicioRegistroCambios()
    proj_id = uuid4()

    page = service.listar_proyecto(proj_id, db=None)
    assert page.source == "postgres_fallback"
    assert len(page.items) == 0
