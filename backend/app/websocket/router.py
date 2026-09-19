from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.connection_manager import manager

router = APIRouter(tags=["websocket"])

ALLOWED_UML_EVENTS = {
    "CREATE_CLASS",
    "UPDATE_CLASS",
    "DELETE_CLASS",
    "CREATE_ATTRIBUTE",
    "UPDATE_ATTRIBUTE",
    "CREATE_METHOD",
    "CREATE_RELATION",
    "CREATE_RELATIONSHIP",
    "MOVE_ELEMENT",
}


@router.websocket("/ws/projects/{project_id}")
async def project_collaboration(websocket: WebSocket, project_id: str) -> None:
    await manager.connect(project_id, websocket)
    await websocket.send_json(
        {
            "type": "SESSION_CONNECTED",
            "project_id": project_id,
            "message": "Sesion colaborativa inicial conectada.",
        }
    )
    try:
        while True:
            event = await websocket.receive_json()
            event_type = event.get("type")
            action = event.get("payload", {}).get("action") if isinstance(event.get("payload"), dict) else None
            if event_type == "UML_EVENT":
                event_type = action
            if event_type not in ALLOWED_UML_EVENTS:
                await websocket.send_json(
                    {
                        "type": "EVENT_REJECTED",
                        "project_id": project_id,
                        "reason": "Evento UML no soportado",
                    }
                )
                continue
            message = {"type": "UML_EVENT", "project_id": project_id, "event": event}
            await manager.broadcast(project_id, message)
            await websocket.send_json({"type": "EVENT_ACK", "project_id": project_id})
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
        return
