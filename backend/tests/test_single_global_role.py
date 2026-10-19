from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import UniqueConstraint

from app.modules.acceso_usuarios.models import Role, User, UserRole
from app.modules.acceso_usuarios.schemas.user import AdminUserUpdateRequest
from app.modules.acceso_usuarios.services.user_service import UserService
from app.modules.modelado_uml.models import UmlDiagram
from app.modules.modelado_uml.schemas.uml import DiagramCreateRequest
from app.modules.modelado_uml.services.uml_service import UmlService
from app.modules.proyectos_colaboracion.schemas.project import ProjectCreateRequest
from app.modules.proyectos_colaboracion.services.project_service import ProjectService


def test_global_role_contract_rejects_project_organizer() -> None:
    with pytest.raises(ValidationError):
        AdminUserUpdateRequest(role_name="ORGANIZADOR")

    assert AdminUserUpdateRequest(role_name="ADMINISTRADOR").role_name == "ADMINISTRADOR"
    assert AdminUserUpdateRequest(role_name="EDITOR").role_name == "EDITOR"


def test_user_role_table_allows_only_one_assignment_per_user() -> None:
    unique_constraints = {
        constraint.name: tuple(column.name for column in constraint.columns)
        for constraint in UserRole.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert unique_constraints["uq_user_roles_user"] == ("user_id",)
    assert "uq_user_roles_user_role" not in unique_constraints


def test_role_update_reuses_the_single_global_assignment() -> None:
    user_id = uuid4()
    editor = Role(id=uuid4(), name="EDITOR", description=None, is_system=True)
    administrator = Role(
        id=uuid4(), name="ADMINISTRADOR", description=None, is_system=True
    )
    assignment = UserRole(user_id=user_id, role_id=editor.id, role=editor)
    user = User(
        id=user_id,
        full_name="Usuario",
        email="user@example.com",
        password_hash="unused",
        is_active=True,
        roles=[assignment],
    )
    db = Mock()
    service = UserService(db)
    service.users = SimpleNamespace(get_by_id=lambda _: user)
    service.roles = SimpleNamespace(get_by_name=lambda _: administrator)
    service.audit = Mock()

    updated = service.update_user(
        user_id,
        AdminUserUpdateRequest(role_name="ADMINISTRADOR"),
        actor_id=uuid4(),
    )

    assert updated.role_names == ["ADMINISTRADOR"]
    assert len(updated.roles) == 1
    assert updated.roles[0].role_id == administrator.id


def test_project_creator_becomes_organizer_only_in_project_membership() -> None:
    owner_id = uuid4()
    project_id = uuid4()
    memberships = []
    db = Mock()
    service = ProjectService(db)

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

    project = service.create_project(
        ProjectCreateRequest(name="Proyecto de prueba"), owner_id=owner_id
    )

    assert project.owner_id == owner_id
    assert len(memberships) == 1
    assert memberships[0].project_id == project_id
    assert memberships[0].user_id == owner_id
    assert memberships[0].project_role == "ORGANIZADOR"
    created_diagrams = [
        call.args[0]
        for call in db.add.call_args_list
        if call.args and isinstance(call.args[0], UmlDiagram)
    ]
    assert len(created_diagrams) == 1
    assert created_diagrams[0].project_id == project_id
    assert created_diagrams[0].name == "Proyecto de prueba"


def test_project_rejects_a_second_diagram() -> None:
    project_id = uuid4()
    existing = UmlDiagram(
        id=uuid4(),
        project_id=project_id,
        created_by_user_id=uuid4(),
        name="Modelo principal",
        diagram_type="class",
        metadata_json={"project_diagram": True},
    )
    service = UmlService(Mock())
    service.members = SimpleNamespace(get_membership=lambda *_: SimpleNamespace())
    service.uml = SimpleNamespace(list_diagrams_by_project=lambda _: [existing])

    with pytest.raises(HTTPException) as error:
        service.create_diagram(
            DiagramCreateRequest(project_id=project_id, name="Segundo diagrama"),
            user_id=uuid4(),
        )

    assert error.value.status_code == 409
    assert error.value.detail["code"] == "PROJECT_DIAGRAM_ALREADY_EXISTS"
