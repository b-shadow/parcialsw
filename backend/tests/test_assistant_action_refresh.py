"""An approved UML change must notify every open canvas in the project."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.modules.asistente_proyecto.routers import rutas_asistente as assistant


def test_confirmed_ai_change_publishes_canvas_refresh(monkeypatch):
    project_id, diagram_id, action_id, user_id = [uuid4() for _ in range(4)]
    action = SimpleNamespace(
        id=action_id,
        action_type="create_attribute",
        payload={"_plan": {"diagram_id": str(diagram_id)}, "name": "id"},
        result_json={"id": str(uuid4())},
    )
    published = []

    class FakeExecutor:
        def __init__(self, db):
            pass

        def confirmar(self, project, proposed_action, user):
            assert (project, proposed_action, user) == (project_id, action_id, user_id)
            return action, False

    class FakePublisher:
        async def publicar_persistido(self, **kwargs):
            published.append(kwargs)

    monkeypatch.setattr(assistant, "ServicioEjecucionAccionesIA", FakeExecutor)
    monkeypatch.setattr(assistant, "PublicadorEventosIAProyecto", FakePublisher)
    monkeypatch.setattr(assistant.RespuestaAccionIA, "model_validate", lambda _: SimpleNamespace(model_dump=lambda **__: {}))
    monkeypatch.setattr(assistant, "RespuestaDecisionAccionIA", lambda **kwargs: SimpleNamespace(**kwargs))

    response = asyncio.run(assistant.confirmar_accion_ia(
        project_id, action_id, SimpleNamespace(id=user_id), None
    ))

    assert response.action is action
    assert [event["event_type"] for event in published] == ["AI_ACTION_STATUS_CHANGED", "UML_EVENT"]
    assert published[1]["diagram_id"] == diagram_id
    assert published[1]["payload"]["action_id"] == str(action_id)
