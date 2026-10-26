"""
WebSocket Broadcaster Service
Maintains connected clients and pushes live furnace telemetry frames.
Queries MySQL furnace_latest once per tick, regardless of how many clients are connected.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

from server.app.config import settings
from server.app.database import SessionLocal
from server.app.models import FurnaceLatest

TAG_META_PATH = Path(__file__).resolve().parent.parent / "tag_meta.json"


class WebSocketBroadcaster:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.tag_meta: Dict[str, Dict[str, Any]] = {}
        self.load_metadata()

    def load_metadata(self):
        if TAG_META_PATH.exists():
            with open(TAG_META_PATH, "r", encoding="utf-8") as f:
                tags = json.load(f)
                self.tag_meta = {t["name"]: t for t in tags}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)

    def build_frame(self, db) -> str:
        """Fetches furnace_latest and produces a serialized JSON broadcast frame."""
        if not self.tag_meta:
            self.load_metadata()

        rows = db.query(FurnaceLatest).all()
        now = datetime.now()
        tags_data = []

        for row in rows:
            meta = self.tag_meta.get(row.tag, {})
            val = row.value
            min_val = meta.get("min")
            max_val = meta.get("max")

            status = "NORMAL"
            if min_val is not None and max_val is not None and not meta.get("cumulative", False):
                if val < min_val or val > max_val:
                    span = max_val - min_val if max_val != min_val else 1.0
                    ratio = (val - max_val) / span if val > max_val else (min_val - val) / span
                    status = "CRITICAL" if ratio >= 0.10 else "WARNING"

            tags_data.append(
                {
                    "tag": row.tag,
                    "value": round(val, 2),
                    "unit": meta.get("unit", ""),
                    "equipment": meta.get("equipment", ""),
                    "min": min_val,
                    "max": max_val,
                    "status": status,
                    "ts": row.ts.isoformat() if row.ts else now.isoformat(),
                }
            )

        frame = {
            "type": "telemetry_update",
            "ts": now.isoformat(),
            "count": len(tags_data),
            "tags": tags_data,
        }
        return json.dumps(frame)

    async def broadcast_loop(self):
        """Infinite loop broadcasting once every WS_PUSH_INTERVAL_SECONDS."""
        print(
            f"[BROADCASTER]: WebSocket broadcaster loop running (Cadence: {settings.WS_PUSH_INTERVAL_SECONDS}s)..."
        )
        while True:
            try:
                # Always query once per tick
                db = SessionLocal()
                try:
                    frame_json = self.build_frame(db)
                finally:
                    db.close()

                # Dispatch concurrently to all active clients
                if self.active_connections:
                    disconnected = []
                    for ws in list(self.active_connections):
                        try:
                            await ws.send_text(frame_json)
                        except (WebSocketDisconnect, ConnectionResetError, Exception):
                            disconnected.append(ws)

                    for ws in disconnected:
                        self.disconnect(ws)

            except Exception as e:
                print(f"[BROADCASTER ERROR]: Error during broadcast cycle: {e}")

            await asyncio.sleep(settings.WS_PUSH_INTERVAL_SECONDS)


broadcaster = WebSocketBroadcaster()
