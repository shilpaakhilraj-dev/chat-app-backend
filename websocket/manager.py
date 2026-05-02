from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[str, List[WebSocket]] = {}  # NEW

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        conns = self.active_connections.get(conversation_id, [])
        if websocket in conns:
            conns.remove(websocket)

    async def broadcast(self, message: dict, conversation_id: str):
        for connection in self.active_connections.get(conversation_id, []):
            await connection.send_json(message)

    # ── NEW: user-level methods ───────────────────────────────────────────────
    async def connect_user(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

    def disconnect_user(self, websocket: WebSocket, user_id: str):
        conns = self.user_connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)

    async def notify_user(self, user_id: str, payload: dict):
        for connection in self.user_connections.get(user_id, []):
            await connection.send_json(payload)

manager = ConnectionManager()