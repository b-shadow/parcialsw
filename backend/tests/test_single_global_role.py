from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import UniqueConstraint

from app.modules.acceso_usuarios.models import Rol, RolUsuario, Usuario
from app.modules.acceso_usuarios.schemas.usuario import SolicitudActualizacionUsuarioAdmin
from app.modules.acceso_usuarios.services.servicio_usuarios import ServicioUsuarios
from app.modules.modelado_uml.models import DiagramaUML
from app.modules.modelado_uml.schemas.uml import SolicitudCreacionDiagrama
from app.modules.modelado_uml.services.servicio_uml import ServicioUML
from app.modules.proyectos_colaboracion.schemas.proyecto import SolicitudCreacionProyecto
from app.modules.proyectos_colaboracion.services.servicio_proyectos import ServicioProyectos


def test_global_role_contract_rejects_project_organizer() -> None:
    with pytest.raises(ValidationError):
        SolicitudActualizacionUsuarioAdmin(role_name="ORGANIZADOR")

    assert SolicitudActualizacionUsuarioAdmin(role_name="ADMINISTRADOR").role_name == "ADMINISTRADOR"
    assert SolicitudActualizacionUsuarioAdmin(role_name="EDITOR").role_name == "EDITOR"


def test_user_role_table_allows_only_one_assignment_per_user() -> None:
    unique_constraints = {
        constraint.name: tuple(column.name for column in constraint.columns)
        for constraint in RolUsuario.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert unique_constraints["uq_roles_usuario_usuario_id"] == ("usuario_id",)
    assert "uq_roles_usuario_usuario_id_rol_id" not in unique_constraints


def test_role_update_reuses_the_single_global_assignment() -> None:
    user_id = uuid4()
    editor = Rol(id=uuid4(), name="EDITOR", description=None, is_system=True)
    administrator = Rol(
        id=uuid4(), name="ADMINISTRADOR", description=None, is_system=True
    )
    assignment = RolUsuario(user_id=user_id, role_id=editor.id, role=editor)
    user = Usuario(
        id=user_id,
        full_name="Usuario",
        email="user@example.com",
        password_hash="unused",
        is_active=True,
        roles=[assignment],
    )
    db = Mock()
    service = ServicioUsuarios(db)
    service.users = SimpleNamespace(obtener_por_id=lambda _: user)
    service.roles = SimpleNamespace(obtener_por_nombre=lambda _: administrator)
    service.audit = Mock()

    updated = service.actualizar_usuario(
        user_id,
        SolicitudActualizacionUsuarioAdmin(role_name="ADMINISTRADOR"),
        actor_id=uuid4(),
    )

    assert updated.nombres_roles == ["ADMINISTRADOR"]
    assert len(updated.roles) == 1
    assert updated.roles[0].role_id == administrator.id


def test_project_creator_becomes_organizer_only_in_project_membership() -> None:
    owner_id = uuid4()
    project_id = uuid4()
    memberships = []
    db = Mock()
    db.info = {}
    service = ServicioProyectos(db)

    def add_project(project):
        project.id = project_id
        return project

    def add_membership(member):
        member.id = uuid4()
        memberships.append(member)
        return member

    service.projects = SimpleNamespace(add=add_project)
    service.members = SimpleNamespace(add=add_membership)
    service.audit = Mock()

    project = service.crear_proyecto(
        SolicitudCreacionProyecto(name="Proyecto de prueba"), owner_id=owner_id
    )

    assert project.owner_id == owner_id
    assert len(memberships) == 1
    assert memberships[0].project_id == project_id
    assert memberships[0].user_id == owner_id
    assert memberships[0].project_role == "ORGANIZADOR"
    created_diagrams = [
        call.args[0]
        for call in db.add.call_args_list
        if call.args and isinstance(call.args[0], DiagramaUML)
    ]
    assert len(created_diagrams) == 1
    assert created_diagrams[0].project_id == project_id
    assert created_diagrams[0].name == "Proyecto de prueba"


def test_project_rejects_a_second_diagram() -> None:
    project_id = uuid4()
    existing = DiagramaUML(
        id=uuid4(),
        project_id=project_id,
        created_by_user_id=uuid4(),
        name="Modelo principal",
        diagram_type="class",
        metadata_json={"project_diagram": True},
    )
    service = ServicioUML(Mock())
    service.db.scalar.return_value = SimpleNamespace(project_role="EDITOR")
    service.members = SimpleNamespace(obtener_participacion=lambda *_: SimpleNamespace(project_role="EDITOR"))
    service.uml = SimpleNamespace(listar_diagramas_por_proyecto=lambda _: [existing])

    with pytest.raises(HTTPException) as error:
        service.crear_diagrama(
            SolicitudCreacionDiagrama(project_id=project_id, name="Segundo diagrama"),
            user_id=uuid4(),
        )

    assert error.value.status_code == 409
    assert error.value.detail["code"] == "PROJECT_DIAGRAM_ALREADY_EXISTS"
