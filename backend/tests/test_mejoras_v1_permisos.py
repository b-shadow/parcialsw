"""Pruebas del sistema de roles y permisos del proyecto (V1.3)."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.asistente_proyecto.models import AccionIA
from app.modules.asistente_proyecto.services.servicio_ejecucion_acciones import (
    ServicioEjecucionAccionesIA,
)
from app.modules.proyectos_colaboracion.models import IntegranteProyecto, Proyecto
from app.modules.proyectos_colaboracion.schemas.proyecto import (
    RespuestaMiParticipacion,
    SolicitudActualizarIntegrante,
    SolicitudAgregarIntegrante,
)
from app.modules.proyectos_colaboracion.services.servicio_proyectos import ServicioProyectos
from app.modules.proyectos_colaboracion.validators.validador_proyecto import (
    asegurar_permiso_proyecto,
)


class MockDbSession:
    def __init__(self, memberships=None, permissions=None):
        self.memberships = memberships or {}  # (project_id, user_id): ProjectMember
        self.permissions = permissions or []
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
    """SolicitudAgregarIntegrante y SolicitudActualizarIntegrante admiten LECTOR y rechazan roles inventados."""
    uid = uuid4()
    req_lector = SolicitudAgregarIntegrante(user_id=uid, project_role="LECTOR")
    assert req_lector.project_role == "LECTOR"

    req_editor = SolicitudAgregarIntegrante(user_id=uid, project_role="EDITOR")
    assert req_editor.project_role == "EDITOR"

    req_org = SolicitudAgregarIntegrante(user_id=uid, project_role="ORGANIZADOR")
    assert req_org.project_role == "ORGANIZADOR"

    with pytest.raises(ValidationError):
        SolicitudAgregarIntegrante(user_id=uid, project_role="ADMIN")

    with pytest.raises(ValidationError):
        SolicitudActualizarIntegrante(project_role="INVITADO")


def test_effective_permissions_and_lector_membership():
    """GET members/me como LECTOR devuelve permissions == ['ai.chat', 'project.read']."""
    proj_id = uuid4()
    user_id = uuid4()

    member_lector = IntegranteProyecto(
        id=uuid4(),
        project_id=proj_id,
        user_id=user_id,
        project_role="LECTOR",
        joined_at=datetime.now(UTC),
    )
    member_lector.permissions = []

    db = MockDbSession()
    db.memberships[(proj_id, user_id)] = member_lector

    service = ServicioProyectos(db)
    service.members = SimpleNamespace(obtener_participacion=lambda pid, uid: member_lector)

    my_mem = service.mi_participacion(proj_id, user_id)
    assert my_mem["project_role"] == "LECTOR"
    assert my_mem["permissions"] == ["ai.chat", "project.read"]

    # Valida el esquema RespuestaMiParticipacion
    resp = RespuestaMiParticipacion.model_validate(my_mem)
    assert resp.permissions == ["ai.chat", "project.read"]


def test_ensure_project_permission_lector_denied_uml_edit():
    """LECTOR no tiene uml.edit y lanza 403 PERMISSION_DENIED."""
    proj_id = uuid4()
    user_id = uuid4()

    member = IntegranteProyecto(
        id=uuid4(),
        project_id=proj_id,
        user_id=user_id,
        project_role="LECTOR",
        joined_at=datetime.now(UTC),
    )
    member.permissions = []

    db = MockDbSession()
    # Mocking RepositorioIntegrantes inside validator
    import app.modules.proyectos_colaboracion.repositories.repositorio_integrantes as mr
    orig_repo = mr.RepositorioIntegrantes
    try:
        class FakeRepo:
            def __init__(self, db_):
                pass
            def obtener_participacion(self, pid, uid):
                if pid == proj_id and uid == user_id:
                    return member
                return None
        mr.RepositorioIntegrantes = FakeRepo

        # LECTOR pidiendo uml.edit -> 403
        with pytest.raises(HTTPException) as exc:
            asegurar_permiso_proyecto(db, proj_id, user_id, "uml.edit")
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "PERMISSION_DENIED"

        # LECTOR pidiendo project.read -> permitido
        m = asegurar_permiso_proyecto(db, proj_id, user_id, "project.read")
        assert m is member
    finally:
        mr.RepositorioIntegrantes = orig_repo


def test_editor_version_permissions_are_fixed():
    """EDITOR no puede restaurar versiones por su rol fijo."""
    proj_id = uuid4()
    user_id = uuid4()

    member_editor = IntegranteProyecto(
        id=uuid4(),
        project_id=proj_id,
        user_id=user_id,
        project_role="EDITOR",
        joined_at=datetime.now(UTC),
    )
    member_editor.permissions = []

    db = MockDbSession()
    import app.modules.proyectos_colaboracion.repositories.repositorio_integrantes as mr
    orig_repo = mr.RepositorioIntegrantes
    try:
        class FakeRepo:
            def __init__(self, db_):
                pass
            def obtener_participacion(self, pid, uid):
                return member_editor
        mr.RepositorioIntegrantes = FakeRepo

        # EDITOR por defecto puede guardar versión (versions.create)
        m = asegurar_permiso_proyecto(db, proj_id, user_id, "versions.create")
        assert m is member_editor

        # EDITOR por defecto NO puede restaurar versión (versions.restore)
        with pytest.raises(HTTPException) as exc:
            asegurar_permiso_proyecto(db, proj_id, user_id, "versions.restore")
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "PERMISSION_DENIED"

        # La lista arbitraria en memoria no amplía los permisos del rol.
        member_editor.permissions = [object()]
        with pytest.raises(HTTPException) as exc:
            asegurar_permiso_proyecto(db, proj_id, user_id, "versions.restore")
        assert exc.value.status_code == 403
    finally:
        mr.RepositorioIntegrantes = orig_repo


def test_ai_confirm_actions_permissions():
    """LECTOR no puede confirmar acciones de IA (403); EDITOR sí puede."""
    proj_id = uuid4()
    lector_id = uuid4()
    editor_id = uuid4()
    action_id = uuid4()

    member_lector = IntegranteProyecto(
        id=uuid4(), project_id=proj_id, user_id=lector_id, project_role="LECTOR"
    )
    member_lector.permissions = []

    member_editor = IntegranteProyecto(
        id=uuid4(), project_id=proj_id, user_id=editor_id, project_role="EDITOR"
    )
    member_editor.permissions = []

    project = Proyecto(id=proj_id, name="Test", owner_id=uuid4(), revision=1)

    db = MockDbSession()
    service = ServicioEjecucionAccionesIA(db)

    # Mock action
    action = AccionIA(
        id=action_id,
        project_id=proj_id,
        requested_by_user_id=lector_id,
        action_type="create_class",
        status="proposed",
        payload={"name": "Cliente"},
    )
    service.repository = SimpleNamespace(
        obtener_accion=lambda pid, aid, for_update=False: action
    )

    import app.modules.proyectos_colaboracion.repositories.repositorio_integrantes as mr
    orig_repo = mr.RepositorioIntegrantes
    try:
        class FakeRepo:
            def __init__(self, db_):
                pass
            def obtener_participacion(self, pid, uid):
                if uid == lector_id:
                    return member_lector
                return member_editor
        mr.RepositorioIntegrantes = FakeRepo

        service.contracts = SimpleNamespace(
            _proyecto_y_miembro=lambda pid, uid: (
                project,
                member_lector if uid == lector_id else member_editor,
            )
        )
        service._verificar_dependencias = lambda a: None
        service._verificar_version_diagrama = lambda a: None
        service._uuid = lambda v: None
        service._ejecutar = lambda a, uid: {"status": "ok"}
        service.uml = SimpleNamespace(
            validar_diagrama=lambda did, uid: SimpleNamespace(model_dump=lambda mode="json": {})
        )

        # LECTOR intentando confirmar -> 403 PERMISSION_DENIED
        with pytest.raises(HTTPException) as exc:
            service.confirmar(proj_id, action_id, lector_id)
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "PERMISSION_DENIED"

        # EDITOR intentando confirmar -> 200 (éxito) y aplica change_origin == 'ai'
        applied_action, _ = service.confirmar(proj_id, action_id, editor_id)
        assert applied_action.status == "applied"
    finally:
        mr.RepositorioIntegrantes = orig_repo
