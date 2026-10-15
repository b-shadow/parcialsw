import asyncio
from collections import defaultdict
from contextlib import suppress

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    MAX_CONNECTIONS_PER_PROJECT = 100
    SEND_TIMEOUT_SECONDS = 5

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)
        self.connection_users: dict[WebSocket, str] = {}
        self.send_locks: dict[WebSocket, asyncio.Lock] = {}

    async def connect(
        self,
        project_id: str,
        websocket: WebSocket,
        user_id: str | None = None,
        subprotocol: str | None = None,
    ) -> bool:
        connections = self.active_connections[project_id]
        if len(connections) >= self.MAX_CONNECTIONS_PER_PROJECT:
            await websocket.close(code=1013, reason="Proyecto con demasiadas conexiones activas")
            return False
        await websocket.accept(subprotocol=subprotocol)
        if websocket not in connections:
            connections.append(websocket)
        self.connection_users[websocket] = user_id or ""
        self.send_locks[websocket] = asyncio.Lock()
        return True

    def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        connections = self.active_connections.get(project_id, [])
        if websocket in connections:
            connections.remove(websocket)
        self.connection_users.pop(websocket, None)
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


manager = ConnectionManager()

