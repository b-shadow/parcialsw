import asyncio
from collections import defaultdict
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect


@dataclass
class ConnectionMetadata:
    connection_id: str
    user_id: str
    display_name: str
    project_role: str
    connected_at: str
    last_seen_at: str
    active_diagram_id: str | None = None


class ConnectionManager:
    MAX_CONNECTIONS_PER_PROJECT = 100
    MAX_CONNECTIONS_PER_USER = 5
    SEND_TIMEOUT_SECONDS = 5

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)
        self.connection_users: dict[WebSocket, str] = {}
        self.connection_metadata: dict[WebSocket, ConnectionMetadata] = {}
        self.send_locks: dict[WebSocket, asyncio.Lock] = {}

    async def connect(
        self,
        project_id: str,
        websocket: WebSocket,
        user_id: str | None = None,
        subprotocol: str | None = None,
        display_name: str = "Usuario",
        project_role: str = "MIEMBRO",
        active_diagram_id: str | None = None,
    ) -> bool:
        connections = self.active_connections[project_id]
        if len(connections) >= self.MAX_CONNECTIONS_PER_PROJECT:
            await websocket.close(code=1013, reason="Proyecto con demasiadas conexiones activas")
            return False
        user_connections = sum(
            1
            for connection in connections
            if self.connection_users.get(connection) == (user_id or "")
        )
        if user_id and user_connections >= self.MAX_CONNECTIONS_PER_USER:
            await websocket.close(code=1013, reason="Demasiadas conexiones para el usuario")
            return False
        await websocket.accept(subprotocol=subprotocol)
        if websocket not in connections:
            connections.append(websocket)
        self.connection_users[websocket] = user_id or ""
        now = datetime.now(UTC).isoformat()
        self.connection_metadata[websocket] = ConnectionMetadata(
            connection_id=str(uuid4()),
            user_id=user_id or "",
            display_name=display_name,
            project_role=project_role,
            connected_at=now,
            last_seen_at=now,
            active_diagram_id=active_diagram_id,
        )
        self.send_locks[websocket] = asyncio.Lock()
        return True

    def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        connections = self.active_connections.get(project_id, [])
        if websocket in connections:
            connections.remove(websocket)
        self.connection_users.pop(websocket, None)
        self.connection_metadata.pop(websocket, None)
        self.send_locks.pop(websocket, None)
        if not connections and project_id in self.active_connections:
            del self.active_connections[project_id]

    async def send(self, project_id: str, websocket: WebSocket, message: dict) -> bool:
        lock = self.send_locks.setdefault(websocket, asyncio.Lock())
        try:
            async with lock:
                await asyncio.wait_for(
                    websocket.send_json(message), timeout=self.SEND_TIMEOUT_SECONDS
                )
            return True
        except (TimeoutError, RuntimeError, WebSocketDisconnect):
            self.disconnect(project_id, websocket)
            with suppress(TimeoutError, RuntimeError):
                await asyncio.wait_for(
                    websocket.close(code=1011, reason="Conexion no disponible"), timeout=1
                )
            return False

    async def broadcast(
        self, project_id: str, message: dict, exclude: WebSocket | None = None
    ) -> None:
        connections = [
            connection
            for connection in list(self.active_connections.get(project_id, []))
            if connection is not exclude
        ]
        if connections:
            await asyncio.gather(
                *(self.send(project_id, connection, message) for connection in connections)
            )

    async def disconnect_user(self, project_id: str, user_id: str) -> None:
        targets = [
            connection
            for connection in list(self.active_connections.get(project_id, []))
            if self.connection_users.get(connection) == user_id
        ]
        for connection in targets:
            try:
                await connection.close(code=1008, reason="Acceso al proyecto revocado")
            except RuntimeError:
                pass
            self.disconnect(project_id, connection)

    def touch(self, websocket: WebSocket, active_diagram_id: str | None = None) -> None:
        metadata = self.connection_metadata.get(websocket)
        if metadata is None:
            return
        metadata.last_seen_at = datetime.now(UTC).isoformat()
        if active_diagram_id is not None:
            metadata.active_diagram_id = active_diagram_id

    def connection(self, websocket: WebSocket) -> dict | None:
        metadata = self.connection_metadata.get(websocket)
        return asdict(metadata) if metadata else None

    def presence(self, project_id: str) -> list[dict]:
        grouped: dict[str, dict] = {}
        for connection in self.active_connections.get(project_id, []):
            metadata = self.connection_metadata.get(connection)
            if metadata is None or not metadata.user_id:
                continue
            current = grouped.get(metadata.user_id)
            if current is None:
                grouped[metadata.user_id] = {
                    "user_id": metadata.user_id,
                    "display_name": metadata.display_name,
                    "project_role": metadata.project_role,
                    "connected_at": metadata.connected_at,
                    "last_seen_at": metadata.last_seen_at,
                    "active_diagram_id": metadata.active_diagram_id,
                    "connection_count": 1,
                }
            else:
                current["connection_count"] += 1
                current["last_seen_at"] = max(
                    current["last_seen_at"], metadata.last_seen_at
                )
                if metadata.active_diagram_id:
                    current["active_diagram_id"] = metadata.active_diagram_id
        return sorted(grouped.values(), key=lambda item: item["display_name"].casefold())

    async def send_to_user(self, project_id: str, user_id: str, message: dict) -> None:
        targets = [
            connection
            for connection in list(self.active_connections.get(project_id, []))
            if self.connection_users.get(connection) == user_id
        ]
        if targets:
            await asyncio.gather(*(self.send(project_id, item, message) for item in targets))


manager = ConnectionManager()

