import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.main import app
from app.modules.asistente_proyecto.schemas.assistant import AiMessagePage, AiReference
from app.modules.asistente_proyecto.services.conversation_memory_service import (
    ConversationMemoryService,
)
from app.websocket.connection_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []
        self.closed: tuple[int, str] | None = None

    async def accept(self, subprotocol: str | None = None) -> None:
        self.subprotocol = subprotocol

    async def send_json(self, message: dict) -> None:
        self.messages.append(message)

    async def close(self, code: int, reason: str) -> None:
        self.closed = (code, reason)


def test_phase3_routes_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "get" in paths["/api/v1/projects/{project_id}/ai/messages"]
    assert "get" in paths["/api/v1/projects/{project_id}/ai/actions"]
    assert "get" in paths["/api/v1/projects/{project_id}/ai/recommendations"]
    assert "patch" in paths[
        "/api/v1/projects/{project_id}/ai/recommendations/{recommendation_id}"
    ]


def test_message_page_exposes_bidirectional_cursor_state() -> None:
    page = AiMessagePage(
        items=[],
        previous_cursor=10,
        next_cursor=20,
        has_more_before=True,
        has_more_after=True,
        min_sequence=11,
        max_sequence=19,
    )
    assert page.has_more_before and page.has_more_after
    assert page.min_sequence == 11
    assert page.max_sequence == 19


def test_references_cover_project_diagram_attribute_and_message() -> None:
    for reference_type in ("project", "diagram", "uml_attribute", "message"):
        reference = AiReference(type=reference_type, id=uuid4(), label="Elemento")
        assert reference.type == reference_type


def test_memory_summary_is_structured_bounded_and_keeps_pending_actions() -> None:
    previous = SimpleNamespace(
        project_goal="Gestionar ventas",
        decisions=["Usaremos UUID"],
        open_questions=[],
        recent_changes=[],
        important_entities=[],
        member_preferences_relevant_to_work=[],
    )
    messages = [
        SimpleNamespace(
            role="user",
            content="Conecta Cliente con Venta? Se define una relacion uno a muchos.",
            detected_intents=["modify_uml"],
            references_json=[{"label": "Cliente"}, {"label": "Venta"}],
        ),
        SimpleNamespace(
            role="assistant",
            content="Se propone la relacion solicitada.",
            detected_intents=[],
            references_json=[],
        ),
    ]
    actions = [SimpleNamespace(action_type="create_relationship", id=uuid4())]

    summary = ConversationMemoryService._deterministic_summary(
        previous, messages, actions, 42
    )

    assert summary.summary_until_sequence == 42
    assert summary.project_goal == "Gestionar ventas"
    assert "Cliente" in summary.important_entities
    assert summary.pending_actions[0].startswith("create_relationship:")
    assert len(summary.decisions) <= 50


def test_presence_aggregates_tabs_and_disconnects_cleanly() -> None:
    async def scenario() -> None:
        manager = ConnectionManager()
        first = FakeWebSocket()
        second = FakeWebSocket()
        await manager.connect(
            "project-a", first, "user-a", display_name="Ana", project_role="EDITOR"
        )  # type: ignore[arg-type]
        await manager.connect(
            "project-a", second, "user-a", display_name="Ana", project_role="EDITOR"
        )  # type: ignore[arg-type]
        manager.touch(first, "diagram-a")  # type: ignore[arg-type]

        presence = manager.presence("project-a")
        assert len(presence) == 1
        assert presence[0]["connection_count"] == 2
        assert presence[0]["active_diagram_id"] == "diagram-a"

        manager.disconnect("project-a", first)  # type: ignore[arg-type]
        assert manager.presence("project-a")[0]["connection_count"] == 1
        manager.disconnect("project-a", second)  # type: ignore[arg-type]
        assert manager.presence("project-a") == []

    asyncio.run(scenario())


def test_connection_manager_limits_tabs_per_user() -> None:
    async def scenario() -> None:
        manager = ConnectionManager()
        manager.MAX_CONNECTIONS_PER_USER = 1
        first = FakeWebSocket()
        rejected = FakeWebSocket()
        assert await manager.connect("project-a", first, "user-a")  # type: ignore[arg-type]
        assert not await manager.connect("project-a", rejected, "user-a")  # type: ignore[arg-type]
        assert rejected.closed == (1013, "Demasiadas conexiones para el usuario")

    asyncio.run(scenario())
