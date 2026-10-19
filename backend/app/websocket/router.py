import json
import time
from collections import deque
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.core.config.settings import settings
from app.core.database.session import SessionLocal
from app.core.security.jwt import decode_access_token
from app.modules.acceso_usuarios.repositories.user_repository import UserRepository
from app.modules.asistente_proyecto.repositories.assistant_repository import AssistantRepository
from app.modules.proyectos_colaboracion.repositories.member_repository import MemberRepository
from app.modules.proyectos_colaboracion.repositories.project_repository import ProjectRepository
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
    "METHOD_SIGNATURE_UPDATED",
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
        project_role = membership.project_role
        current_project_sequence = ProjectRepository(db).current_event_sequence(project_uuid)
        conversation = AssistantRepository(db).get_conversation(project_uuid)
        current_conversation_sequence = conversation.last_message_sequence if conversation else 0

    user_was_present = any(
        manager.connection_users.get(item) == str(user_id)
        for item in manager.active_connections.get(project_id, [])
    )
    connected = await manager.connect(
        project_id,
        websocket,
        str(user_id),
        subprotocol="case-v1" if "case-v1" in offered_protocols else None,
        display_name=user_name,
        project_role=project_role,
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
            "connection_id": (manager.connection(websocket) or {}).get("connection_id"),
            "project_sequence": current_project_sequence,
            "conversation_sequence": current_conversation_sequence,
        },
    )
    presence = manager.presence(project_id)
    if not user_was_present:
        await manager.broadcast(
            project_id,
            {
                "protocol_version": 2,
                "type": "PRESENCE_JOINED",
                "event_id": str(uuid4()),
                "project_id": project_id,
                "sequence_number": 0,
                "conversation_sequence": current_conversation_sequence,
                "correlation_id": str(uuid4()),
                "occurred_at": datetime.now(UTC).isoformat(),
                "persistent": False,
                "actor": {"user_id": str(user_id), "display_name": user_name},
                "payload": {"member": next(
                    (item for item in presence if item["user_id"] == str(user_id)), None
                )},
            },
            exclude=websocket,
        )
    await manager.broadcast(
        project_id,
        {
            "protocol_version": 2,
            "type": "PRESENCE_SNAPSHOT",
            "event_id": str(uuid4()),
            "project_id": project_id,
            "sequence_number": 0,
            "conversation_sequence": current_conversation_sequence,
            "correlation_id": str(uuid4()),
            "occurred_at": datetime.now(UTC).isoformat(),
            "persistent": False,
            "actor": {"user_id": str(user_id), "display_name": user_name},
            "payload": {"members": presence},
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
                active_diagram = _optional_uuid(event.get("active_diagram_id"))
                manager.touch(
                    websocket, str(active_diagram) if active_diagram else None
                )
                continue
            if event_type == "SYNC_STATE":
                last_project_sequence = event.get("last_project_sequence")
                last_conversation_sequence = event.get("last_conversation_sequence")
                with SessionLocal() as db:
                    project_sequence = ProjectRepository(db).current_event_sequence(project_uuid)
                    current_conversation = AssistantRepository(db).get_conversation(project_uuid)
                    conversation_sequence = (
                        current_conversation.last_message_sequence if current_conversation else 0
                    )
                if (
                    isinstance(last_project_sequence, int)
                    and last_project_sequence < project_sequence
                ) or (
                    isinstance(last_conversation_sequence, int)
                    and last_conversation_sequence < conversation_sequence
                ):
                    await manager.send(
                        project_id,
                        websocket,
                        {
                            "protocol_version": 2,
                            "type": "SYNC_REQUIRED",
                            "event_id": str(uuid4()),
                            "project_id": project_id,
                            "sequence_number": project_sequence,
                            "conversation_sequence": conversation_sequence,
                            "correlation_id": str(uuid4()),
                            "occurred_at": datetime.now(UTC).isoformat(),
                            "persistent": False,
                            "actor": {"user_id": str(user_id), "display_name": user_name},
                            "payload": {
                                "after_project_sequence": last_project_sequence or 0,
                                "after_conversation_sequence": last_conversation_sequence or 0,
                            },
                        },
                    )
                continue
            if event_type == "ACTIVE_DIAGRAM":
                diagram_value = _optional_uuid(event.get("diagram_id"))
                manager.touch(websocket, str(diagram_value) if diagram_value else None)
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
        was_last_connection = sum(
            1
            for item in manager.active_connections.get(project_id, [])
            if manager.connection_users.get(item) == str(user_id)
        ) <= 1
        manager.disconnect(project_id, websocket)
        if was_last_connection:
            await manager.broadcast(
                project_id,
                {
                    "protocol_version": 2,
                    "type": "PRESENCE_LEFT",
                    "event_id": str(uuid4()),
                    "project_id": project_id,
                    "sequence_number": 0,
                    "conversation_sequence": None,
                    "correlation_id": str(uuid4()),
                    "occurred_at": datetime.now(UTC).isoformat(),
                    "persistent": False,
                    "actor": {"user_id": str(user_id), "display_name": user_name},
                    "payload": {"user_id": str(user_id)},
                },
            )
        await manager.broadcast(
            project_id,
            {
                "protocol_version": 2,
                "type": "PRESENCE_SNAPSHOT",
                "event_id": str(uuid4()),
                "project_id": project_id,
                "sequence_number": 0,
                "conversation_sequence": None,
                "correlation_id": str(uuid4()),
                "occurred_at": datetime.now(UTC).isoformat(),
                "persistent": False,
                "actor": {"user_id": str(user_id), "display_name": user_name},
                "payload": {"members": manager.presence(project_id)},
            },
        )
