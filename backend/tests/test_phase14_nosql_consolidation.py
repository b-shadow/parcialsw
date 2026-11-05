import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config.configuracion import settings
from app.core.nosql.cliente import EstadoMongo
from app.core.nosql.commands.consolidar import ControlConsolidacion
from app.core.nosql.commands.respaldo_coordinado import _decode, _encode
from app.core.nosql.conciliacion import ServicioConciliacion, canonical_sha256
from app.core.nosql.contratos import ColeccionMongo
from app.core.nosql.errores import ErrorMongoNoDisponible
from app.main import app, crear_aplicacion
from app.modules.generacion_software.services.servicio_generacion import ServicioGeneracion
from app.modules.modelado_uml.engine.modelo_interno import ModeloDiagramaUML
from app.modules.modelado_uml.models import ClaseUML, DiagramaUML, ElementoVisualUML
from app.modules.modelado_uml.repositories.repositorio_mongo_uml import RepositorioMongoUML
from app.modules.modelado_uml.services.almacen_diagrama_activo import (
    SYNC_PROJECTS_KEY,
    AlmacenDocumentosUMLActivo,
    marcar_proyecto_uml_para_sincronizar,
)
from app.modules.proyectos_colaboracion.schemas.proyecto import SolicitudCreacionProyecto
from app.modules.proyectos_colaboracion.services.servicio_proyectos import ServicioProyectos


class AsyncCursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def __aiter__(self):
        self.iterator = iter(self.rows)
        return self

    async def __anext__(self):
        try:
            return next(self.iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    def sort(self, *_args, **_kwargs):
        return self


class FakeCollection:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.insert_one = AsyncMock()

    def find(self, *_args, **_kwargs):
        return AsyncCursor(self.rows)

    async def index_information(self):
        return {"_id_": {"key": [("_id", 1)]}}

    async def find_one(self, *_args, **_kwargs):
        return self.rows[0] if self.rows else None

    async def count_documents(self, *_args, **_kwargs):
        return len(self.rows)

    async def find_one_and_replace(self, _filter, payload, **_kwargs):
        return payload


class FakeDatabase(dict):
    async def command(self, _command):
        return {"ok": 1}


def _uml_document(diagram_id, project_id, *, revision=3):
    content = ModeloDiagramaUML(
        id=str(diagram_id),
        project_id=str(project_id),
        name="Consolidado",
    ).model_dump(mode="json")
    return {
        "_id": str(diagram_id),
        "project_id": str(project_id),
        "schema_version": 1,
        "revision": revision,
        "content": content,
        "content_hash": canonical_sha256(content),
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


def test_phase14_strict_uml_read_never_builds_sql_projection(monkeypatch) -> None:
    diagram_id, project_id = uuid4(), uuid4()
    document = _uml_document(diagram_id, project_id)
    store = AlmacenDocumentosUMLActivo(
        database={
            ColeccionMongo.UML_DIAGRAMS.value: SimpleNamespace(find_one=lambda _query: document)
        }
    )
    db = MagicMock()
    db.scalar.return_value = 3
    diagram = SimpleNamespace(id=diagram_id, project_id=project_id)
    monkeypatch.setattr(settings, "uml_diagrams_mongodb_read_enabled", True)
    monkeypatch.setattr(settings, "uml_diagrams_sql_fallback_enabled", False)
    monkeypatch.setattr(settings, "uml_diagrams_compare_reads", False)

    with patch(
        "app.modules.modelado_uml.services.almacen_diagrama_activo.construir_modelo_diagrama_sql"
    ) as sql_projection:
        model = store.modelo_para(db, diagram)

    assert model.name == "Consolidado"
    sql_projection.assert_not_called()


def test_phase14_operational_audit_detects_revision_lag_and_persists(monkeypatch) -> None:
    project_id, diagram_id = uuid4(), uuid4()
    database = FakeDatabase(
        {
            ColeccionMongo.UML_DIAGRAMS.value: FakeCollection(
                [_uml_document(diagram_id, project_id, revision=2)]
            ),
            ColeccionMongo.UML_DIAGRAM_VERSIONS.value: FakeCollection(),
            ColeccionMongo.AI_MESSAGES.value: FakeCollection(),
            ColeccionMongo.AI_CONTEXT_SNAPSHOTS.value: FakeCollection(),
            ColeccionMongo.OPERATIONAL_AUDITS.value: FakeCollection(),
        }
    )
    db = MagicMock()
    db.execute.side_effect = [
        SimpleNamespace(tuples=lambda: [(project_id, 3)]),
        SimpleNamespace(tuples=lambda: [(diagram_id, project_id)]),
        SimpleNamespace(tuples=list),
        SimpleNamespace(tuples=list),
    ]
    db.scalars.side_effect = [[], []]
    monkeypatch.setattr(settings, "nosql_alert_max_revision_lag", 0)

    report = asyncio.run(ServicioConciliacion(db, database).audit_operational())

    assert report["status"] == "degraded"
    assert any(item["code"] == "REVISION_LAG" for item in report["findings"])
    assert report["metrics"]["max_revision_lag"] == 1
    database[ColeccionMongo.OPERATIONAL_AUDITS.value].insert_one.assert_awaited_once()


def test_operational_audit_detects_message_gap_with_matching_count() -> None:
    conversation_id, project_id = uuid4(), uuid4()
    database = FakeDatabase(
        {
            ColeccionMongo.UML_DIAGRAMS.value: FakeCollection(),
            ColeccionMongo.UML_DIAGRAM_VERSIONS.value: FakeCollection(),
            ColeccionMongo.AI_MESSAGES.value: FakeCollection(
                [
                    {
                        "_id": str(uuid4()),
                        "conversation_id": str(conversation_id),
                        "project_id": str(project_id),
                        "sequence_number": sequence,
                    }
                    for sequence in (1, 3)
                ]
            ),
            ColeccionMongo.AI_CONTEXT_SNAPSHOTS.value: FakeCollection(),
            ColeccionMongo.OPERATIONAL_AUDITS.value: FakeCollection(),
        }
    )
    db = MagicMock()
    db.execute.side_effect = [
        SimpleNamespace(tuples=lambda: [(project_id, 0)]),
        SimpleNamespace(tuples=list),
        SimpleNamespace(tuples=lambda: [(conversation_id, 2)]),
        SimpleNamespace(tuples=list),
    ]
    db.scalars.side_effect = [[], []]

    report = asyncio.run(ServicioConciliacion(db, database).audit_operational())

    assert any(item["code"] == "MISSING_CONVERSATION_MESSAGES" for item in report["findings"])


def test_phase14_backup_encoding_roundtrip_preserves_database_types() -> None:
    value = {
        "id": uuid4(),
        "created_at": datetime.now(UTC),
        "amount": Decimal("19.95"),
        "payload": b"case-inteligente",
        "nested": [{"enabled": True}],
        "user_json": {"__case_type__": "uuid", "value": "not-a-backup-tag"},
    }

    assert _decode(_encode(value)) == value


def test_phase14_consolidated_mode_keeps_canonical_publication_when_dual_write_is_off(
    monkeypatch,
) -> None:
    project_id = uuid4()
    db = SimpleNamespace(info={})
    monkeypatch.setattr(settings, "uml_diagrams_dual_write_enabled", False)
    monkeypatch.setattr(settings, "nosql_consolidated_mode", True)

    marcar_proyecto_uml_para_sincronizar(db, project_id)

    assert db.info[SYNC_PROJECTS_KEY] == {project_id}


def test_phase14_document_repository_roundtrips_embedded_uml_content() -> None:
    project_id, diagram_id, class_id, attribute_id, method_id, parameter_id = (
        uuid4() for _ in range(6)
    )
    diagram = DiagramaUML(
        id=diagram_id,
        project_id=project_id,
        created_by_user_id=uuid4(),
        name="Ventas",
        diagram_type="class",
        status="active",
        current_version=1,
        metadata_json={},
    )
    source = ModeloDiagramaUML.model_validate({
        "id": str(diagram_id),
        "project_id": str(project_id),
        "name": "Ventas",
        "classes": [{
            "id": str(class_id),
            "name": "Cliente",
            "attributes": [{
                "id": str(attribute_id),
                "name": "correo",
                "data_type": "String",
            }],
            "methods": [{
                "id": str(method_id),
                "name": "registrar",
                "return_type": "void",
                "parameters": [{
                    "id": str(parameter_id),
                    "name": "email",
                    "data_type": "String",
                }],
            }],
            "visual": {"x": 120, "y": 80},
        }],
    })
    repository = RepositorioMongoUML.__new__(RepositorioMongoUML)
    repository.cache = {}
    repository._reconstruir(source, diagram)

    restored = repository.model(diagram)

    assert restored.id == source.id
    assert restored.classes[0].name == "Cliente"
    assert restored.classes[0].visual.x == 120
    assert repository.obtener_atributo(attribute_id).name == "correo"
    assert repository.obtener_metodo(method_id).parameters[0].id == parameter_id


def test_phase14_sql_foreign_keys_do_not_target_mongodb_messages() -> None:
    from app.modules.asistente_proyecto.models import AccionIA, RecomendacionIA

    for model in (AccionIA, RecomendacionIA):
        foreign_keys = model.__table__.c.mensaje_origen_id.foreign_keys
        assert not foreign_keys


def test_generation_uses_mongodb_uml_repository() -> None:
    service = ServicioGeneracion(MagicMock())
    assert isinstance(service.uml, RepositorioMongoUML)


def test_missing_mongodb_diagram_is_not_treated_as_empty() -> None:
    diagram_id = uuid4()
    repository = RepositorioMongoUML.__new__(RepositorioMongoUML)
    repository.cache = {}
    repository.documents = MagicMock()
    repository.documents.get.return_value = None
    repository.obtener_diagrama = MagicMock(return_value=SimpleNamespace(id=diagram_id))

    with pytest.raises(HTTPException) as exc:
        repository._estado(diagram_id)

    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "UML_DOCUMENT_MISSING"


def test_unavailable_mongodb_diagram_returns_service_unavailable() -> None:
    diagram_id = uuid4()
    repository = RepositorioMongoUML.__new__(RepositorioMongoUML)
    repository.cache = {}
    repository.documents = MagicMock()
    repository.documents.get.side_effect = ErrorMongoNoDisponible("offline")
    repository.obtener_diagrama = MagicMock(return_value=SimpleNamespace(id=diagram_id))

    with pytest.raises(HTTPException) as exc:
        repository._estado(diagram_id)

    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "UML_DOCUMENT_UNAVAILABLE"


def test_new_class_with_unset_visual_style_can_be_saved_to_mongodb() -> None:
    uml_class = ClaseUML(
        id=uuid4(), diagram_id=uuid4(), name="Cliente",
        visibility="public", element_type="class", metadata_json={},
    )
    uml_class.attributes = []
    uml_class.methods = []
    visual = ElementoVisualUML(
        id=uuid4(), diagram_id=uml_class.diagram_id,
        element_type="class", element_id=uml_class.id,
        position_x=100, position_y=200,
    )

    model = RepositorioMongoUML._modelo_clase(uml_class, visual)

    assert model.visual.style == {}


def test_new_project_initializes_its_diagram_in_mongo_cache() -> None:
    db = MagicMock()
    db.info = {}
    db.add.side_effect = lambda item: setattr(item, "id", uuid4()) if item.id is None else None
    project = SimpleNamespace(id=uuid4(), name="Proyecto de prueba", description="UML")
    service = ServicioProyectos(db)
    service.projects.add = MagicMock(return_value=project)
    service.members.add = MagicMock(return_value=SimpleNamespace(id=uuid4()))
    service.audit.record = MagicMock()

    service.crear_proyecto(SolicitudCreacionProyecto(name=project.name), uuid4())

    cache = db.info["mongo_uml_repository"]
    assert len(cache) == 1
    assert next(iter(cache.values()))["classes"] == {}


def test_unhandled_api_error_keeps_cors_header() -> None:
    application = crear_aplicacion()

    @application.get("/test-unhandled-error")
    def fail():
        raise RuntimeError("test failure")

    response = TestClient(application, raise_server_exceptions=False).get(
        "/test-unhandled-error",
        headers={"Origin": "http://127.0.0.1:5173"},
    )

    assert response.status_code == 500
    assert response.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5173"
    assert response.json()["detail"]["code"] == "INTERNAL_SERVER_ERROR"


def test_phase14_gate_refuses_incomplete_migrations_and_degraded_audit(monkeypatch) -> None:
    migrations = FakeCollection()
    audits = FakeCollection()
    database = FakeDatabase(
        {
            ColeccionMongo.MIGRATION_CHECKPOINTS.value: migrations,
            ColeccionMongo.OPERATIONAL_AUDITS.value: audits,
        }
    )
    session = MagicMock()
    session.scalar.return_value = 2
    session_context = MagicMock()
    session_context.__enter__.return_value = session
    session_context.__exit__.return_value = False
    monkeypatch.setattr(settings, "ai_messages_migration_required", True)
    monkeypatch.setattr(settings, "uml_versions_migration_required", True)
    monkeypatch.setattr(settings, "uml_diagrams_migration_required", True)

    with (
        patch(
            "app.core.nosql.commands.consolidar.SessionLocal",
            return_value=session_context,
        ),
        patch(
            "app.core.nosql.commands.consolidar.ServicioConciliacion.audit_operational",
            AsyncMock(return_value={"status": "degraded", "findings": []}),
        ),
    ):
        report = asyncio.run(ControlConsolidacion(database).evaluate())

    assert report["status"] == "blocked"
    assert set(report["blockers"]) == {
        "operational_audit_degraded",
        "outbox_not_drained",
        "required_migrations_incomplete",
        "insufficient_stability_window",
    }


def test_phase14_readiness_requires_fresh_audit_and_consolidation(monkeypatch) -> None:
    checkpoints = SimpleNamespace(find_one=AsyncMock(return_value={"status": "completed"}))
    audits = SimpleNamespace(
        find_one=AsyncMock(
            return_value={
                "status": "healthy",
                "created_at": datetime.now(UTC),
            }
        )
    )
    database = {
        ColeccionMongo.MIGRATION_CHECKPOINTS.value: checkpoints,
        ColeccionMongo.OPERATIONAL_AUDITS.value: audits,
    }
    health = EstadoMongo(status="available", required=True, database="case_test")
    monkeypatch.setattr(settings, "phase14_consolidation_required", True)
    monkeypatch.setattr(settings, "nosql_reconciliation_required", True)

    with (
        patch("app.main.SessionLocal", MagicMock()),
        patch.object(app.state.mongo_manager, "ping", AsyncMock(return_value=health)),
        patch.object(app.state.mongo_manager, "_database", database),
    ):
        response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json()["components"]["phase14_consolidation"]["status"] == "completed"
    assert response.json()["components"]["nosql_reconciliation"]["status"] == "healthy"
