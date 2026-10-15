import json
import time
from collections import deque
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.core.security.jwt import decode_access_token
from app.modules.acceso_usuarios.repositories.user_repository import UserRepository
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.services.project_service import ProjectService
from app.websocket.connection_manager import manager

router = APIRouter(tags=["websocket"])

ALLOWED_UML_EVENTS = {
    "CREATE_CLASS",
    "UPDATE_CLASS",
    "DELETE_CLASS",
    "CREATE_ATTRIBUTE",
    "UPDATE_ATTRIBUTE",
    "CREATE_METHOD",
    "UPDATE_METHOD",
    "DELETE_METHOD",
    "CREATE_RELATION",
    "CREATE_RELATIONSHIP",
    "UPDATE_RELATIONSHIP",
    "DELETE_RELATIONSHIP",
    "DELETE_ATTRIBUTE",
    "AI_UPDATE_DIAGRAM",
    "MOVE_ELEMENT",
}
MAX_EVENT_BYTES = 64 * 1024
MAX_EVENTS_PER_WINDOW = 100
RATE_WINDOW_SECONDS = 10


def _optional_uuid(value: object) -> UUID | None:
    try:
        return UUID(str(value)) if value else None
    except ValueError:
        return None


def _element_data(payload: dict) -> tuple[str | None, UUID | None]:
    candidates = (
        ("class", "class_id"),
        ("attribute", "attribute_id"),
        ("method", "method_id"),
        ("relationship", "relationship_id"),
    )
    for element_type, key in candidates:
        element_id = _optional_uuid(payload.get(key))
        if element_id is not None:
            return element_type, element_id
    return None, None


@router.websocket("/ws/projects/{project_id}")
async def project_collaboration(websocket: WebSocket, project_id: str) -> None:
    origin = websocket.headers.get("origin")
    allowed_origins = {value.rstrip("/") for value in settings.cors_origins}
    if origin and origin.rstrip("/") not in allowed_origins:
        await websocket.close(code=1008, reason="Origen WebSocket no permitido")
        return
    offered_protocols = [
        value.strip()
        for value in websocket.headers.get("sec-websocket-protocol", "").split(",")
    ]
    auth_protocol = next(
        (value for value in offered_protocols if value.startswith("case-auth.")), None
    )
    token = auth_protocol.removeprefix("case-auth.") if auth_protocol else ""
    try:
        project_uuid = UUID(project_id)
        user_id = decode_access_token(token)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Credenciales invalidas")
        return

    with SessionLocal() as db:
        user = UserRepository(db).get_by_id(user_id)
        membership = MemberRepository(db).get_membership(project_uuid, user_id)
        if user is None or not user.is_active or membership is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Sin acceso al proyecto")
            return
        user_name = user.full_name

    connected = await manager.connect(
        project_id,
        websocket,
        str(user_id),
        subprotocol="case-v1" if "case-v1" in offered_protocols else None,
    )
    if not connected:
        return
    await manager.send(
        project_id,
        websocket,
        {
            "type": "SESSION_CONNECTED",
            "project_id": project_id,
            "user_id": str(user_id),
            "user_name": user_name,
            "message": "Sesion colaborativa inicial conectada.",
        },
    )
    try:
        recent_events: deque[float] = deque()
        while True:
            try:
                event = await websocket.receive_json()
            except (TypeError, ValueError):
                await manager.send(
                    project_id,
                    websocket,
                    {"type": "EVENT_REJECTED", "reason": "Mensaje JSON invalido"},
                )
                continue
            if not isinstance(event, dict):
                await manager.send(
                    project_id,
                    websocket,
                    {"type": "EVENT_REJECTED", "reason": "Formato de evento invalido"},
                )
                continue
            if len(json.dumps(event, separators=(",", ":")).encode("utf-8")) > MAX_EVENT_BYTES:
                await websocket.close(code=1009, reason="Evento demasiado grande")
                return
            event_type = event.get("type")
            if event_type == "PING":
                try:
                    current_user_id = decode_access_token(token)
                except ValueError:
                    await websocket.close(code=1008, reason="Sesion expirada")
                    return
                with SessionLocal() as db:
                    current_user = UserRepository(db).get_by_id(current_user_id)
                    current_membership = MemberRepository(db).get_membership(
                        project_uuid, current_user_id
                    )
                    if (
                        current_user is None
                        or not current_user.is_active
                        or current_membership is None
                    ):
                        await websocket.close(code=1008, reason="Acceso al proyecto revocado")
                        return
                await manager.send(
                    project_id,
                    websocket,
                    {"type": "PONG", "server_time": datetime.now(UTC).isoformat()},
                )
                continue
            now = time.monotonic()
            recent_events.append(now)
            while recent_events and recent_events[0] < now - RATE_WINDOW_SECONDS:
                recent_events.popleft()
            if len(recent_events) > MAX_EVENTS_PER_WINDOW:
                await websocket.close(code=1008, reason="Demasiados eventos colaborativos")
                return
            action = event.get("payload", {}).get("action") if isinstance(event.get("payload"), dict) else None
            if event_type == "UML_EVENT":
                event_type = action
            if event_type not in ALLOWED_UML_EVENTS:
                await manager.send(
                    project_id,
                    websocket,
                    {
                        "type": "EVENT_REJECTED",
                        "project_id": project_id,
                        "reason": "Evento UML no soportado",
                    },
                )
                continue
            payload = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
            client_event_id = _optional_uuid(payload.get("client_event_id"))
            if client_event_id is None:
                await manager.send(
                    project_id,
                    websocket,
                    {
                        "type": "EVENT_REJECTED",
                        "project_id": project_id,
                        "reason": "El evento no incluye un client_event_id valido",
                    },
                )
                continue
            diagram_id = _optional_uuid(payload.get("diagram_id"))
            element_type, element_id = _element_data(payload)
            try:
                with SessionLocal() as db:
                    stored_event, was_created = ProjectService(db).record_collaboration_event(
                        project_id=project_uuid,
                        diagram_id=diagram_id,
                        user_id=user_id,
                        client_event_id=client_event_id,
                        event_type=event_type,
                        element_type=element_type,
                        element_id=element_id,
                        base_version=payload.get("base_version")
                        if isinstance(payload.get("base_version"), int)
                        else None,
                        payload=payload,
                    )
            except HTTPException as exc:
                await manager.send(
                    project_id,
                    websocket,
                    {
                        "type": "EVENT_REJECTED",
                        "project_id": project_id,
                        "client_event_id": str(client_event_id),
                        "reason": str(exc.detail),
                    },
                )
                continue
            message = {
                "type": "UML_EVENT",
                "project_id": project_id,
                "diagram_id": str(diagram_id) if diagram_id else None,
                "event_id": str(stored_event.id),
                "client_event_id": str(stored_event.client_event_id),
                "sequence_number": stored_event.sequence_number,
                "event_type": event_type,
                "payload": payload,
                "user_id": str(user_id),
                "user_name": user_name,
                "created_at": stored_event.created_at.isoformat(),
            }
            if was_created:
                await manager.broadcast(project_id, message, exclude=websocket)
            await manager.send(
                project_id,
                websocket,
                {
                    "type": "EVENT_ACK",
                    "project_id": project_id,
                    "event_id": str(stored_event.id),
                    "client_event_id": str(stored_event.client_event_id),
                    "sequence_number": stored_event.sequence_number,
                    "duplicate": not was_created,
                },
            )
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(project_id, websocket)
