"""Pruebas del sistema de roles y permisos del proyecto (V1.3)."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.asistente_proyecto.models import AiAction
from app.modules.asistente_proyecto.services.action_execution_service import (
    AiActionExecutionService,
)
from app.modules.proyectos_colaboracion.models import Project, ProjectMember, ProjectPermission
from app.modules.proyectos_colaboracion.schemas.project import (
    AddMemberRequest,
    MyMembershipResponse,
    PermissionRequest,
    UpdateMemberRequest,
)
from app.modules.proyectos_colaboracion.services.project_service import ProjectService
from app.modules.proyectos_colaboracion.validators.project_validator import (
    ensure_project_permission,
)


class MockDbSession:
    def __init__(self, memberships=None, permissions=None):
        self.memberships = memberships or {}  # (project_id, user_id): ProjectMember
        self.permissions = permissions or []   # list of ProjectPermission
        self.info = {}

    def scalar(self, query):
        return None

    def scalars(self, query):
        class Result:
            def all(self):
                return []
        return Result()

    def add(self, obj):
        pass

    def commit(self):
        pass

    def flush(self):
        pass

    def refresh(self, obj):
        pass

    def delete(self, obj):
        pass


def test_schema_validates_lector_and_rejects_admin():
    """AddMemberRequest y UpdateMemberRequest admiten LECTOR y rechazan roles inventados."""
    uid = uuid4()
    req_lector = AddMemberRequest(user_id=uid, project_role="LECTOR")
    assert req_lector.project_role == "LECTOR"

    req_editor = AddMemberRequest(user_id=uid, project_role="EDITOR")
    assert req_editor.project_role == "EDITOR"

    req_org = AddMemberRequest(user_id=uid, project_role="ORGANIZADOR")
    assert req_org.project_role == "ORGANIZADOR"

    with pytest.raises(ValidationError):
        AddMemberRequest(user_id=uid, project_role="ADMIN")

    with pytest.raises(ValidationError):
        UpdateMemberRequest(project_role="INVITADO")


def test_effective_permissions_and_lector_membership():
    """GET members/me como LECTOR devuelve permissions == ['ai.chat', 'project.read']."""
    proj_id = uuid4()
    user_id = uuid4()

    member_lector = ProjectMember(
        id=uuid4(),
        project_id=proj_id,
        user_id=user_id,
        project_role="LECTOR",
        joined_at=datetime.now(UTC),
    )
    member_lector.permissions = []

    db = MockDbSession()
    db.memberships[(proj_id, user_id)] = member_lector

    service = ProjectService(db)
    service.members = SimpleNamespace(get_membership=lambda pid, uid: member_lector)

    my_mem = service.my_membership(proj_id, user_id)
    assert my_mem["project_role"] == "LECTOR"
    assert my_mem["permissions"] == ["ai.chat", "project.read"]

    # Valida el esquema MyMembershipResponse
    resp = MyMembershipResponse.model_validate(my_mem)
    assert resp.permissions == ["ai.chat", "project.read"]


def test_ensure_project_permission_lector_denied_uml_edit():
    """LECTOR no tiene uml.edit y lanza 403 PERMISSION_DENIED."""
    proj_id = uuid4()
    user_id = uuid4()

    member = ProjectMember(
        id=uuid4(),
        project_id=proj_id,
        user_id=user_id,
        project_role="LECTOR",
        joined_at=datetime.now(UTC),
    )
    member.permissions = []

    db = MockDbSession()
    # Mocking MemberRepository inside validator
    import app.modules.proyectos_colaboracion.repositories.member_repository as mr
    orig_repo = mr.MemberRepository
    try:
        class FakeRepo:
            def __init__(self, db_):
                pass
            def get_membership(self, pid, uid):
                if pid == proj_id and uid == user_id:
                    return member
                return None
        mr.MemberRepository = FakeRepo

        # LECTOR pidiendo uml.edit -> 403
        with pytest.raises(HTTPException) as exc:
            ensure_project_permission(db, proj_id, user_id, "uml.edit")
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "PERMISSION_DENIED"

        # LECTOR pidiendo project.read -> permitido
        m = ensure_project_permission(db, proj_id, user_id, "project.read")
        assert m is member
    finally:
        mr.MemberRepository = orig_repo


def test_editor_version_permissions_and_granted_override():
    """EDITOR no puede restaurar por defecto (403), pero con permiso otorgado sí puede (200)."""
    proj_id = uuid4()
    user_id = uuid4()

    member_editor = ProjectMember(
        id=uuid4(),
        project_id=proj_id,
        user_id=user_id,
        project_role="EDITOR",
        joined_at=datetime.now(UTC),
    )
    member_editor.permissions = []

    db = MockDbSession()
    import app.modules.proyectos_colaboracion.repositories.member_repository as mr
    orig_repo = mr.MemberRepository
    try:
        class FakeRepo:
            def __init__(self, db_):
                pass
            def get_membership(self, pid, uid):
                return member_editor
        mr.MemberRepository = FakeRepo

        # EDITOR por defecto puede guardar versión (versions.create)
        m = ensure_project_permission(db, proj_id, user_id, "versions.create")
        assert m is member_editor

        # EDITOR por defecto NO puede restaurar versión (versions.restore)
        with pytest.raises(HTTPException) as exc:
            ensure_project_permission(db, proj_id, user_id, "versions.restore")
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "PERMISSION_DENIED"

        # Concedemos permiso versions.restore
        granted_perm = ProjectPermission(
            id=uuid4(),
            member_id=member_editor.id,
            permission_code="versions.restore",
            is_allowed=True,
        )
        member_editor.permissions = [granted_perm]

        # Ahora el EDITOR sí puede restaurar versión
        m_restored = ensure_project_permission(db, proj_id, user_id, "versions.restore")
        assert m_restored is member_editor
    finally:
        mr.MemberRepository = orig_repo


def test_ai_confirm_actions_permissions():
    """LECTOR no puede confirmar acciones de IA (403); EDITOR sí puede."""
    proj_id = uuid4()
    lector_id = uuid4()
    editor_id = uuid4()
    action_id = uuid4()

    member_lector = ProjectMember(
        id=uuid4(), project_id=proj_id, user_id=lector_id, project_role="LECTOR"
    )
    member_lector.permissions = []

    member_editor = ProjectMember(
        id=uuid4(), project_id=proj_id, user_id=editor_id, project_role="EDITOR"
    )
    member_editor.permissions = []

    project = Project(id=proj_id, name="Test", owner_id=uuid4(), revision=1)

    db = MockDbSession()
    service = AiActionExecutionService(db)

    # Mock action
    action = AiAction(
        id=action_id,
        project_id=proj_id,
        requested_by_user_id=lector_id,
        action_type="create_class",
        status="proposed",
        payload={"name": "Cliente"},
    )
    service.repository = SimpleNamespace(
        get_action=lambda pid, aid, for_update=False: action
    )

    import app.modules.proyectos_colaboracion.repositories.member_repository as mr
    orig_repo = mr.MemberRepository
    try:
        class FakeRepo:
            def __init__(self, db_):
                pass
            def get_membership(self, pid, uid):
                if uid == lector_id:
                    return member_lector
                return member_editor
        mr.MemberRepository = FakeRepo

        service.contracts = SimpleNamespace(
            _project_and_member=lambda pid, uid: (
                project,
                member_lector if uid == lector_id else member_editor,
            )
        )
        service._ensure_dependencies = lambda a: None
        service._ensure_diagram_version = lambda a: None
        service._uuid = lambda v: None
        service._execute = lambda a, uid: {"status": "ok"}
        service.uml = SimpleNamespace(
            validate_diagram=lambda did, uid: SimpleNamespace(model_dump=lambda mode="json": {})
        )

        # LECTOR intentando confirmar -> 403 PERMISSION_DENIED
        with pytest.raises(HTTPException) as exc:
            service.confirm(proj_id, action_id, lector_id)
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "PERMISSION_DENIED"

        # EDITOR intentando confirmar -> 200 (éxito) y aplica change_origin == 'ai'
        applied_action, _ = service.confirm(proj_id, action_id, editor_id)
        assert applied_action.status == "applied"
    finally:
        mr.MemberRepository = orig_repo


def test_set_permission_validates_code():
    """POST members/{id}/permissions valida códigos contra PERMISSION_CODES (422 si no)."""
    proj_id = uuid4()
    org_id = uuid4()
    member_id = uuid4()

    db = MockDbSession()
    service = ProjectService(db)

    # Código inválido -> 422
    payload_bad = PermissionRequest(permission_code="inventado.code", is_allowed=True)
    with pytest.raises(HTTPException) as exc:
        service.set_permission(proj_id, member_id, payload_bad, org_id)
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "INVALID_PERMISSION_CODE"
