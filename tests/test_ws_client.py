"""
Short Python WebSocket Test Client
Connects to /api/ws, prints 3 telemetry frames, then exits cleanly.
"""
import asyncio
import json
import os
import sys
import requests
import websockets

SERVER_HTTP_URL = os.getenv("SERVER_URL", "http://127.0.0.1:8000")
SERVER_WS_URL = os.getenv("WS_URL", "ws://127.0.0.1:8000/api/ws")
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "Admin@Secure2026!")

async def test_websocket_stream():
    print(f"Authenticating with {SERVER_HTTP_URL}...")
    try:
        r = requests.post(
            f"{SERVER_HTTP_URL}/api/auth/login",
            json={"username": ADMIN_USER, "password": ADMIN_PASS},
            timeout=3.0
        )
        token = r.json()["access_token"]
    except Exception as e:
        print(f"[ERROR]: Could not authenticate to obtain token: {e}")
        return

    ws_target = f"{SERVER_WS_URL}?token={token}"
    print(f"Connecting to WebSocket at {SERVER_WS_URL}...")
    async with websockets.connect(ws_target) as ws:
        print("Connected! Listening for 3 live broadcast frames:")
        for i in range(1, 4):
            message = await ws.recv()
            data = json.loads(message)
            tag_count = len(data.get("tags", []))
            sample_tag = data.get("tags", [{}])[0]
            print(
                f"[Frame {i}/3 | {data.get('ts')}]: "
                f"{tag_count} tags received. Sample: {sample_tag.get('tag')} = {sample_tag.get('value')} {sample_tag.get('unit')} ({sample_tag.get('status')})"
            )

    print("Successfully received 3 frames. WebSocket test completed.")

if __name__ == "__main__":
    asyncio.run(test_websocket_stream())
