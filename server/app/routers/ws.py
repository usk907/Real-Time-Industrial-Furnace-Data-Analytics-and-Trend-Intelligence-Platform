"""
WebSocket Telemetry Streaming Endpoint
Validates JWT on handshake, subscribes connection to broadcaster, and handles lifecycle.
"""

from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from server.app.auth import decode_access_token
from server.app.services.broadcaster import broadcaster

router = APIRouter(tags=["WebSocket"])


@router.websocket("/api/ws")
async def websocket_telemetry_stream(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    Real-time SCADA telemetry push via WebSocket.
    Authenticates token query parameter; rejects invalid tokens with custom close code 4401.
    Receives broadcast frames generated once per second from the shared broadcaster service.
    """
    if not token:
        await websocket.close(code=4401, reason="Authentication token required")
        return

    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not username:
            await websocket.close(code=4401, reason="Invalid token claims")
            return
    except Exception:
        await websocket.close(code=4401, reason="Invalid authentication token")
        return

    # Valid token: accept connection and register with broadcaster
    await broadcaster.connect(websocket)
    try:
        while True:
            # Keep listener open for client heartbeats or messages
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, ConnectionResetError):
        pass
    finally:
        broadcaster.disconnect(websocket)
