from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.modules.acceso_usuarios.services.servicio_auditoria import sanear_metadatos_auditoria
from app.modules.notificaciones.models import (
    BandejaSalidaNotificacion,
    Notificacion,
    PreferenciaNotificacion,
)
from app.modules.notificaciones.schemas.notificacion import EnlaceProfundoNotificacion
from app.modules.notificaciones.services.servicio_notificaciones import (
    EventoNotificacionDominio,
    ServicioNotificaciones,
)
from app.modules.proyectos_colaboracion.schemas.instantanea import (
    InstantaneaProyecto,
    InstantaneaProyectoV2,
    hash_instantanea_sha256,
    normalizar_instantanea_proyecto,
)
from app.modules.proyectos_colaboracion.services.servicio_proyectos import (
    EVENT_ALIASES,
    ServicioProyectos,
)


def snapshot(*, captured_at: datetime, diagrams: list[dict] | None = None) -> InstantaneaProyectoV2:
    return InstantaneaProyectoV2(
        captured_at=captured_at,
        project=InstantaneaProyecto(id=uuid4(), name="Ventas"),
        diagrams=diagrams or [],
    )


def test_snapshot_hash_is_deterministic_and_excludes_capture_time() -> None:
    project_id = uuid4()
    first = InstantaneaProyectoV2(
        captured_at=datetime(2026, 1, 1, tzinfo=UTC),
        project=InstantaneaProyecto(id=project_id, name="Ventas"),
        diagrams=[{"id": "b"}, {"id": "a"}],
    )
    second = InstantaneaProyectoV2(
        captured_at=datetime(2026, 10, 1, tzinfo=UTC),
        project=InstantaneaProyecto(id=project_id, name="Ventas"),
        diagrams=[{"id": "a"}, {"id": "b"}],
    )
    assert normalizar_instantanea_proyecto(first) == normalizar_instantanea_proyecto(second)
    assert hash_instantanea_sha256(first) == hash_instantanea_sha256(second)
    assert len(hash_instantanea_sha256(first)) == 64


def test_snapshot_contract_rejects_unknown_restore_fields() -> None:
    value = snapshot(captured_at=datetime.now(UTC)).model_dump(mode="json")
    value["access_token"] = "must-not-enter"
    with pytest.raises(ValidationError):
        InstantaneaProyectoV2.model_validate(value)


def test_audit_metadata_is_recursive_bounded_and_secret_free() -> None:
    cleaned = sanear_metadatos_auditoria({
        "operation": "restore",
        "nested": {"authorization": "Bearer secret", "safe": "x" * 900},
        "private_key": "hidden",
    })
    assert cleaned == {"operation": "restore", "nested": {"safe": "x" * 500}}


def test_deep_links_only_accept_closed_internal_routes() -> None:
    valid = EnlaceProfundoNotificacion(
        route_name="project_collaborative", params={"project_id": str(uuid4())}
    )
    assert valid.route_name == "project_collaborative"
    with pytest.raises(ValidationError):
        EnlaceProfundoNotificacion(route_name="https://attacker.example")


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def scalar(self, _statement):
        return None

    def scalars(self, _statement):
        return []

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        for value in self.added:
            if getattr(value, "id", None) is None:
                value.id = uuid4()


def test_notification_policy_creates_inbox_and_outbox_but_excludes_actor() -> None:
    actor = uuid4()
    recipient = uuid4()
    session = FakeSession()
    created = ServicioNotificaciones(session).record(  # type: ignore[arg-type]
        EventoNotificacionDominio(
            type="PROJECT_VERSION_RESTORED",
            category="versions",
            title="Proyecto restaurado",
            body="Se restauro una version.",
            recipient_user_ids={actor, recipient},
            dedup_entity_id=uuid4(),
            actor_user_id=actor,
            deep_link=EnlaceProfundoNotificacion(route_name="projects"),
        )
    )
    assert len(created) == 1
    assert created[0].recipient_user_id == recipient
    assert sum(isinstance(item, Notificacion) for item in session.added) == 1
    assert sum(isinstance(item, BandejaSalidaNotificacion) for item in session.added) == 1


def test_global_notification_preferences_have_database_uniqueness() -> None:
    index = next(
        item for item in PreferenciaNotificacion.__table__.indexes
        if item.name == "ix_preferencias_notificaciones_usuario_id_categoria"
    )
    assert index.unique is True
    assert str(index.dialect_options["postgresql"]["where"]) == "proyecto_id IS NULL"


def test_snapshot_statistics_cover_uml_content() -> None:
    value = snapshot(
        captured_at=datetime.now(UTC),
        diagrams=[{
            "id": str(uuid4()),
            "classes": [
                {"attributes": [{}, {}], "methods": [{}]},
                {"attributes": [], "methods": [{}, {}]},
            ],
            "relationships": [{}, {}],
        }],
    )
    assert ServicioProyectos._estadisticas_instantanea(value) == {
        "diagrams": 1, "classes": 2, "attributes": 2, "methods": 3, "relationships": 2,
    }


def test_phase7_event_aliases_are_canonical() -> None:
    assert EVENT_ALIASES["CREATE_CLASS"] == "UML_CLASS_CREATED"
    assert EVENT_ALIASES["RESTORE_VERSION"] == "PROJECT_VERSION_RESTORED"


def test_phase7_routes_are_exposed_in_openapi() -> None:
    document = TestClient(app).get("/openapi.json").json()
    paths = document["paths"]
    expected = {
        "/api/v1/projects/{project_id}/activity",
        "/api/v1/projects/{project_id}/versions/{version_id}/restore-preview",
        "/api/v1/notifications",
        "/api/v1/notifications/unread-count",
        "/api/v1/notifications/{notification_id}/read",
        "/api/v1/notifications/read-all",
        "/api/v1/notifications/preferences",
    }
    assert expected <= set(paths)
    assert "snapshot" not in document["components"]["schemas"]["RespuestaVersion"]["properties"]
