from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config.configuracion import settings
from app.modules.modelado_uml.services.almacen_diagrama_activo import SYNC_PROJECTS_KEY
from app.modules.proyectos_colaboracion.models import Proyecto
from app.modules.proyectos_colaboracion.services.guardia_mutaciones_proyecto import GuardiaMutacionesProyecto


def test_project_revision_change_schedules_uml_document_sync(monkeypatch):
    monkeypatch.setattr(settings, "nosql_consolidated_mode", True)
    project = Proyecto(id=uuid4(), revision=2)
    with Session() as db:
        db.add(project)
        assert GuardiaMutacionesProyecto.avanzar(project) == 3
        assert db.info[SYNC_PROJECTS_KEY] == {project.id}
