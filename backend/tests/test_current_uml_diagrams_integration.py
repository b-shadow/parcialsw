"""Persistencia actual del diagrama: identidad SQL y contenido MongoDB."""

import asyncio
import os
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text

from app.core.config.configuracion import settings
from app.core.database.sesion import SessionLocal, engine
from app.core.nosql.cliente import mongo_manager
from app.core.nosql.cliente_sincrono import sync_mongo_manager
from app.core.nosql.contratos import ColeccionMongo
from app.modules.acceso_usuarios.models import Usuario
from app.modules.modelado_uml.schemas.uml import (
    SolicitudActualizacionClaseUML,
    SolicitudCreacionClaseUML,
)
from app.modules.modelado_uml.services.servicio_uml import ServicioUML
from app.modules.proyectos_colaboracion.schemas.proyecto import SolicitudCreacionProyecto
from app.modules.proyectos_colaboracion.services.servicio_proyectos import ServicioProyectos

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("MONGODB_TEST_URI"),
    reason="Se requieren PostgreSQL y MongoDB aislados",
)


def test_diagrama_actual_actualiza_contenido_mongo_y_referencia_sql() -> None:
    assert settings.database_url.rsplit("/", 1)[-1].endswith("test")
    assert settings.mongodb_database.endswith("test")

    async def scenario() -> None:
        assert (await mongo_manager.connect(bootstrap=True)).available
        try:
            with SessionLocal() as db:
                user = Usuario(
                    full_name="Prueba UML",
                    email=f"uml-{uuid4()}@example.com",
                    password_hash="unused",
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                project = ServicioProyectos(db).crear_proyecto(
                    SolicitudCreacionProyecto(name="Diagrama de prueba"), user.id
                )
                uml = ServicioUML(db)
                diagram = uml.listar_diagramas(project.id, user.id)[0]
                created = uml.crear_clase(
                    diagram.id, SolicitudCreacionClaseUML(name="Estudiante"), user.id
                )
                uml.actualizar_clase(
                    created.id, SolicitudActualizacionClaseUML(name="Alumno"), user.id
                )
                assert {item.name for item in uml.listar_clases(diagram.id, user.id)} == {"Alumno"}
                assert db.scalar(text("SELECT proyecto_id FROM diagramas_uml WHERE id = :id"),
                                 {"id": diagram.id}) == project.id
                stored = sync_mongo_manager.database[ColeccionMongo.UML_DIAGRAMS.value].find_one(
                    {"_id": str(diagram.id)}
                )
                assert stored["project_id"] == str(project.id)
                assert [item["name"] for item in stored["content"]["classes"]] == ["Alumno"]
                assert "uml_classes" not in inspect(engine).get_table_names()
        finally:
            sync_mongo_manager.close()
            await mongo_manager.close()

    asyncio.run(scenario())
