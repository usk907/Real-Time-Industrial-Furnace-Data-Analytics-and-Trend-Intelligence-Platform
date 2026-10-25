from fastapi import WebSocket
from typing import List
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS]: Client connected. Active sessions: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[WS]: Client disconnected. Active sessions: {len(self.active_connections)}")

    async def broadcast(self, data: dict):
        """Send JSON payload to all active browser screens."""
        message = json.dumps(data)
        stale_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                stale_connections.append(connection)
                
        # Clean up broken sockets
        for conn in stale_connections:
            self.disconnect(conn)

ws_manager = WebSocketManager()
