import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.modelado_uml.services.uml_service import UmlService
from app.modules.proyectos_colaboracion.services.project_service import ProjectService
from app.modules.proyectos_colaboracion.validators.project_validator import ensure_organizer
from app.websocket.connection_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.messages: list[dict] = []
        self.closed: tuple[int, str] | None = None

    async def accept(self, subprotocol: str | None = None) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.messages.append(message)

    async def close(self, code: int, reason: str) -> None:
        self.closed = (code, reason)


def test_collaboration_broadcast_is_project_scoped_and_excludes_sender() -> None:
    async def scenario() -> None:
        manager = ConnectionManager()
        sender = FakeWebSocket()
        collaborator = FakeWebSocket()
        other_project = FakeWebSocket()

        await manager.connect("project-a", sender)  # type: ignore[arg-type]
        await manager.connect("project-a", collaborator)  # type: ignore[arg-type]
        await manager.connect("project-b", other_project)  # type: ignore[arg-type]
        await manager.broadcast(
            "project-a",
            {"type": "UML_EVENT", "event_type": "UPDATE_CLASS"},
            exclude=sender,  # type: ignore[arg-type]
        )

        assert sender.messages == []
        assert collaborator.messages == [
            {"type": "UML_EVENT", "event_type": "UPDATE_CLASS"}
        ]
        assert other_project.messages == []

    asyncio.run(scenario())


def test_only_organizer_can_manage_saved_versions() -> None:
    organizer = SimpleNamespace(project_role="ORGANIZADOR")
    editor = SimpleNamespace(project_role="EDITOR")

    assert ensure_organizer(organizer) is organizer
    with pytest.raises(HTTPException) as rejected:
        ensure_organizer(editor)
    assert rejected.value.status_code == 403


def test_connection_manager_limits_connections_per_project() -> None:
    async def scenario() -> None:
        manager = ConnectionManager()
        manager.MAX_CONNECTIONS_PER_PROJECT = 1
        first = FakeWebSocket()
        rejected = FakeWebSocket()

        assert await manager.connect("project-a", first)  # type: ignore[arg-type]
        assert not await manager.connect("project-a", rejected)  # type: ignore[arg-type]
        assert rejected.closed == (1013, "Proyecto con demasiadas conexiones activas")

    asyncio.run(scenario())


def test_duplicate_client_event_is_acknowledged_without_creating_another() -> None:
    project_id = uuid4()
    user_id = uuid4()
    client_event_id = uuid4()
    existing = SimpleNamespace(client_event_id=client_event_id, sequence_number=7)
    service = object.__new__(ProjectService)
    service.members = SimpleNamespace(
        get_membership=lambda requested_project_id, requested_user_id: SimpleNamespace(
            project_role="EDITOR"
        )
    )
    service.projects = SimpleNamespace(
        get_for_update=lambda requested_project_id: SimpleNamespace(id=project_id),
        get_event_by_client_id=lambda requested_project_id, requested_user_id, requested_event_id: existing,
    )

    event, was_created = service.record_collaboration_event(
        project_id=project_id,
        diagram_id=None,
        user_id=user_id,
        client_event_id=client_event_id,
        event_type="UPDATE_CLASS",
        element_type="class",
        element_id=uuid4(),
        base_version=None,
        payload={},
    )

    assert event is existing
    assert was_created is False


def test_restore_rejects_malformed_snapshot_before_changing_diagrams() -> None:
    service = object.__new__(UmlService)
    service.members = SimpleNamespace(
        get_membership=lambda project_id, user_id: SimpleNamespace(project_role="ORGANIZADOR")
    )

    with pytest.raises(HTTPException) as rejected:
        service.restore_project_snapshot(
            uuid4(),
            {"schema_version": 1, "diagrams": [{"id": "invalid"}]},
            uuid4(),
        )

    assert rejected.value.status_code == 422


def test_collaboration_event_rejects_diagram_from_another_project() -> None:
    project_id = uuid4()
    service = object.__new__(ProjectService)
    service.members = SimpleNamespace(
        get_membership=lambda requested_project_id, user_id: SimpleNamespace(project_role="EDITOR")
    )
    service.db = SimpleNamespace(
        get=lambda model, diagram_id: SimpleNamespace(project_id=uuid4())
    )

    with pytest.raises(HTTPException) as rejected:
        service.record_collaboration_event(
            project_id=project_id,
            diagram_id=uuid4(),
            user_id=uuid4(),
            client_event_id=uuid4(),
            event_type="UPDATE_CLASS",
            element_type="class",
            element_id=uuid4(),
            base_version=None,
            payload={},
        )

    assert rejected.value.status_code == 400
