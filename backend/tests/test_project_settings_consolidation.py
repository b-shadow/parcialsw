from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.generacion_software.schemas.contrato_temas import DEFAULT_THEME_V2
from app.modules.generacion_software.schemas.temas import ActualizacionTemaFlutter
from app.modules.generacion_software.services.servicio_temas import ServicioTemas
from app.modules.proyectos_colaboracion.models import Proyecto


def test_flutter_theme_keeps_independent_revision_inside_project_settings():
    project_id, user_id = uuid4(), uuid4()
    project = Proyecto(
        id=project_id, owner_id=user_id, name="Tema", settings={"ai": {"enabled": False}},
        revision=3, created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
    )

    class Db:
        def get(self, model, ident):
            return project

        def scalar(self, statement):
            return project

        def commit(self):
            pass

        def rollback(self):
            pass

    service = ServicioTemas(Db())
    service._require_member = lambda *_: None
    service._requerir_editor = lambda *_: None
    service.audit = SimpleNamespace(record=lambda **_: None)
    payload = ActualizacionTemaFlutter(config=DEFAULT_THEME_V2.model_dump(mode="json"))

    first = service.put(project_id, payload, user_id, expected_revision=0)
    assert first.revision == 1
    assert project.revision == 4
    assert project.settings["ai"] == {"enabled": False}

    with pytest.raises(HTTPException) as conflict:
        service.put(project_id, payload, user_id, expected_revision=0)
    assert conflict.value.status_code == 409

    same = service.put(project_id, payload, user_id, expected_revision=1)
    assert same.revision == 1
    assert project.revision == 4
