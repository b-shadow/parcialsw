"""Pruebas completas del sistema de invitaciones al proyecto (V2.3)."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.modules.acceso_usuarios.models import User
from app.modules.proyectos_colaboracion.models import Project, ProjectMember
from app.modules.proyectos_colaboracion.models.project_invitation import ProjectInvitation
from app.modules.proyectos_colaboracion.schemas.invitation import InvitationCreateRequest
from app.modules.proyectos_colaboracion.services.invitation_service import (
    InvitationService,
)


def test_routes_registered_in_openapi():
    """Verifica que las 6 rutas de invitaciones estén expuestas en OpenAPI."""
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]

    # 1. POST /api/v1/projects/{project_id}/invitations
    assert "/api/v1/projects/{project_id}/invitations" in paths
    assert "post" in paths["/api/v1/projects/{project_id}/invitations"]

    # 2. GET /api/v1/projects/{project_id}/invitations
    assert "get" in paths["/api/v1/projects/{project_id}/invitations"]

    # 3. DELETE /api/v1/projects/{project_id}/invitations/{invitation_id}
    assert "/api/v1/projects/{project_id}/invitations/{invitation_id}" in paths
    assert "delete" in paths["/api/v1/projects/{project_id}/invitations/{invitation_id}"]

    # 4. GET /api/v1/invitations/me
    assert "/api/v1/invitations/me" in paths
    assert "get" in paths["/api/v1/invitations/me"]

    # 5. POST /api/v1/invitations/{invitation_id}/accept
    assert "/api/v1/invitations/{invitation_id}/accept" in paths
    assert "post" in paths["/api/v1/invitations/{invitation_id}/accept"]

    # 6. POST /api/v1/invitations/{invitation_id}/reject
    assert "/api/v1/invitations/{invitation_id}/reject" in paths
    assert "post" in paths["/api/v1/invitations/{invitation_id}/reject"]


class FakeDb:
    def __init__(self, projects=None, members=None, invitations=None, users=None):
        self._projects = {p.id: p for p in (projects or [])}
        self._members = {(m.project_id, m.user_id): m for m in (members or [])}
        self._invitations = {i.id: i for i in (invitations or [])}
        self._users = {u.id: u for u in (users or [])}
        self._users_by_email = {u.email.lower(): u for u in (users or [])}
        self.info = {}
        self.notifications_recorded = []

    def get(self, model, ident):
        if model == Project:
            return self._projects.get(ident)
        if model == User:
            return self._users.get(ident)
        if model == ProjectInvitation:
            return self._invitations.get(ident)
        if model == ProjectMember:
            for m in self._members.values():
                if getattr(m, "id", None) == ident:
                    return m
            return None
        return None

    def scalar(self, statement):
        sql = str(statement).lower()
        criteria_values = [
            getattr(c.right, "value", None)
            for c in getattr(statement, "_where_criteria", [])
            if hasattr(c, "right")
        ]
        if "project_members" in sql:
            for (pid, uid), m in self._members.items():
                if pid in criteria_values and uid in criteria_values:
                    return m
            return None
        if "users" in sql:
            for val in criteria_values:
                if isinstance(val, str) and val.lower() in self._users_by_email:
                    return self._users_by_email[val.lower()]
            return None
        if "project_invitations" in sql:
            for inv in self._invitations.values():
                if inv.project_id in criteria_values and any(
                    isinstance(v, str) and inv.invited_email.lower() == v.lower()
                    for v in criteria_values
                ):
                    return inv
            return None
        return None

    def scalars(self, statement):
        class Res:
            def __init__(self, items):
                self._items = items
            def all(self):
                return self._items
            def __iter__(self):
                return iter(self._items)
        return Res([])

    def add(self, obj):
        if isinstance(obj, ProjectInvitation):
            self._invitations[obj.id] = obj
        elif isinstance(obj, ProjectMember):
            self._members[(obj.project_id, obj.user_id)] = obj

    def flush(self):
        pass

    def commit(self):
        pass

    def refresh(self, obj):
        pass


@pytest.fixture
def test_setup():
    project_id = uuid4()
    org_user_id = uuid4()
    editor_user_id = uuid4()
    invitee_user_id = uuid4()
    other_user_id = uuid4()

    org_user = User(id=org_user_id, email="org@uagrm.edu.bo", full_name="Organizador")
    editor_user = User(id=editor_user_id, email="editor@uagrm.edu.bo", full_name="Editor")
    invitee_user = User(id=invitee_user_id, email="invitado@uagrm.edu.bo", full_name="Invitado")
    other_user = User(id=other_user_id, email="otro@uagrm.edu.bo", full_name="Otro")

    project = Project(id=project_id, name="CASE Inteligente", owner_id=org_user_id)

    org_member = ProjectMember(
        id=uuid4(), project_id=project_id, user_id=org_user_id, project_role="ORGANIZADOR"
    )
    editor_member = ProjectMember(
        id=uuid4(), project_id=project_id, user_id=editor_user_id, project_role="EDITOR"
    )

    db = FakeDb(
        projects=[project],
        members=[org_member, editor_member],
        users=[org_user, editor_user, invitee_user, other_user],
    )

    service = InvitationService(db)
    # Configure repos
    service.invitations.add = lambda inv: db.add(inv) or inv
    service.invitations.get = lambda iid: db._invitations.get(iid)
    service.invitations.pending_for = lambda pid, em: next(
        (i for i in db._invitations.values() if i.project_id == pid and i.invited_email.lower() == em.lower() and i.status == "pending"),
        None,
    )
    service.invitations.list_by_project = lambda pid, st=None: [
        i for i in db._invitations.values() if i.project_id == pid and (st is None or i.status == st)
    ]
    service.invitations.list_pending_for_email = lambda em: [
        i for i in db._invitations.values() if i.invited_email.lower() == em.lower() and i.status == "pending"
    ]

    service.projects.get = lambda pid: db._projects.get(pid)
    service.members.get_membership = lambda pid, uid: db._members.get((pid, uid))
    service.members.add = lambda m: db.add(m) or m

    # Activity/Audit mocks for project_service
    service.project_service.audit = SimpleNamespace(record=lambda **kw: None)
    service.project_service._activity_event = lambda **kw: None

    return SimpleNamespace(
        db=db,
        service=service,
        project_id=project_id,
        org_user=org_user,
        editor_user=editor_user,
        invitee_user=invitee_user,
        other_user=other_user,
    )


def test_organizer_invites_email_success(test_setup):
    """Organizador invita a un correo → 201, pending, expires_at a 7 días."""
    ctx = test_setup
    payload = InvitationCreateRequest(email="invitado@uagrm.edu.bo", project_role="EDITOR")
    inv = ctx.service.invite(ctx.project_id, payload, ctx.org_user.id)

    assert inv.status == "pending"
    assert inv.project_role == "EDITOR"
    assert inv.invited_email == "invitado@uagrm.edu.bo"
    assert inv.invited_by_user_id == ctx.org_user.id
    assert inv.expires_at is not None

    diff = inv.expires_at - datetime.now(UTC)
    assert 6.9 < diff.total_seconds() / 86400 <= 7.1

    resp = ctx.service.to_response(inv)
    assert resp.project_name == "CASE Inteligente"
    assert resp.invited_by_name == "Organizador"


def test_invite_same_email_case_insensitive_raises_409(test_setup):
    """Mismo correo con otra mayúscula → 409 INVITATION_ALREADY_PENDING."""
    ctx = test_setup
    payload1 = InvitationCreateRequest(email="nuevo@uagrm.edu.bo", project_role="EDITOR")
    ctx.service.invite(ctx.project_id, payload1, ctx.org_user.id)

    # Reintento con mayúsculas
    payload2 = InvitationCreateRequest(email="NUEVO@UAGRM.EDU.BO", project_role="LECTOR")
    with pytest.raises(HTTPException) as exc:
        ctx.service.invite(ctx.project_id, payload2, ctx.org_user.id)

    assert exc.value.status_code == 409
    assert exc.value.detail == "INVITATION_ALREADY_PENDING"


def test_invite_existing_member_raises_409(test_setup):
    """Invitar a un integrante existente → 409 MEMBER_ALREADY_EXISTS."""
    ctx = test_setup
    payload = InvitationCreateRequest(email=ctx.editor_user.email, project_role="EDITOR")

    with pytest.raises(HTTPException) as exc:
        ctx.service.invite(ctx.project_id, payload, ctx.org_user.id)

    assert exc.value.status_code == 409
    assert exc.value.detail == "MEMBER_ALREADY_EXISTS"


def test_editor_invites_raises_403(test_setup):
    """Editor invita → 403 PERMISSION_DENIED."""
    ctx = test_setup
    payload = InvitationCreateRequest(email="alguien@uagrm.edu.bo", project_role="EDITOR")

    with pytest.raises(HTTPException) as exc:
        ctx.service.invite(ctx.project_id, payload, ctx.editor_user.id)

    assert exc.value.status_code == 403


def test_invitee_accepts_creates_member_and_notifies_inviter(test_setup, monkeypatch):
    """Invitado acepta → integrante con el rol y notificación al que invitó."""
    ctx = test_setup
    notifications = []

    import app.modules.proyectos_colaboracion.services.invitation_service as is_mod
    monkeypatch.setattr(
        is_mod,
        "NotificationService",
        lambda db_: SimpleNamespace(record=lambda ev: notifications.append(ev)),
    )

    payload = InvitationCreateRequest(email=ctx.invitee_user.email, project_role="LECTOR")
    inv = ctx.service.invite(ctx.project_id, payload, ctx.org_user.id)

    member = ctx.service.accept(inv.id, ctx.invitee_user)
    assert member is not None
    assert member.project_role == "LECTOR"
    assert member.user_id == ctx.invitee_user.id
    assert inv.status == "accepted"

    accepted_notifs = [n for n in notifications if n.type == "PROJECT_INVITATION_ACCEPTED"]
    assert len(accepted_notifs) == 1
    assert ctx.org_user.id in accepted_notifs[0].recipient_user_ids


def test_different_user_accepts_raises_404(test_setup):
    """Otro usuario intenta aceptar → 404 INVITATION_NOT_FOUND."""
    ctx = test_setup
    payload = InvitationCreateRequest(email=ctx.invitee_user.email, project_role="EDITOR")
    inv = ctx.service.invite(ctx.project_id, payload, ctx.org_user.id)

    with pytest.raises(HTTPException) as exc:
        ctx.service.accept(inv.id, ctx.other_user)

    assert exc.value.status_code == 404
    assert exc.value.detail == "INVITATION_NOT_FOUND"


def test_expired_invitation_raises_410_and_status_expired(test_setup):
    """Invitación con expires_at pasado → aceptar 410 y estado expired."""
    ctx = test_setup
    payload = InvitationCreateRequest(email=ctx.invitee_user.email, project_role="EDITOR")
    inv = ctx.service.invite(ctx.project_id, payload, ctx.org_user.id)

    inv.expires_at = datetime.now(UTC) - timedelta(hours=1)

    with pytest.raises(HTTPException) as exc:
        ctx.service.accept(inv.id, ctx.invitee_user)

    assert exc.value.status_code == 410
    assert exc.value.detail == "INVITATION_EXPIRED"
    assert inv.status == "expired"


def test_revoke_invitation_removes_from_mine(test_setup):
    """Revocar → 204 y ya no aparece en invitations/me."""
    ctx = test_setup
    payload = InvitationCreateRequest(email=ctx.invitee_user.email, project_role="EDITOR")
    inv = ctx.service.invite(ctx.project_id, payload, ctx.org_user.id)

    mine_before = ctx.service.list_mine(ctx.invitee_user)
    assert any(item.id == inv.id for item in mine_before)

    ctx.service.revoke(ctx.project_id, inv.id, ctx.org_user.id)
    assert inv.status == "revoked"

    mine_after = ctx.service.list_mine(ctx.invitee_user)
    assert not any(item.id == inv.id for item in mine_after)
