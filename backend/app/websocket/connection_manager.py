from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[project_id].append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        connections = self.active_connections.get(project_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and project_id in self.active_connections:
            del self.active_connections[project_id]

    async def broadcast(self, project_id: str, message: dict) -> None:
        for connection in list(self.active_connections.get(project_id, [])):
            await connection.send_json(message)


manager = ConnectionManager()

