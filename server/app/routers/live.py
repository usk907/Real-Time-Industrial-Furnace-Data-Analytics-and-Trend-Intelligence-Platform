"""
Live Telemetry Endpoints
Provides real-time tag snapshots from furnace_latest joined with tag_meta.json.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.app.auth import get_current_user
from server.app.database import get_db
from server.app.models import FurnaceLatest, User
from server.app.schemas import LiveResponse, TagLiveItem

router = APIRouter(prefix="/api/live", tags=["Live Telemetry"])
TAG_META_PATH = Path(__file__).resolve().parent.parent / "tag_meta.json"

_tag_meta_cache: Dict[str, Dict[str, Any]] = {}


def get_tag_metadata() -> Dict[str, Dict[str, Any]]:
    global _tag_meta_cache
    if not _tag_meta_cache and TAG_META_PATH.exists():
        with open(TAG_META_PATH, "r", encoding="utf-8") as f:
            tags = json.load(f)
            _tag_meta_cache = {t["name"]: t for t in tags}
    return _tag_meta_cache


@router.get("", response_model=LiveResponse)
def get_live_telemetry(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Returns latest telemetry readings for all furnace tags from furnace_latest,
    joined with unit, min, max, equipment, and live status.
    Requires authenticated user.
    """
    meta_map = get_tag_metadata()
    rows = db.query(FurnaceLatest).all()
    now = datetime.now()

    tag_items = []
    for row in rows:
        meta = meta_map.get(row.tag, {})
        val = row.value
        min_val = meta.get("min")
        max_val = meta.get("max")

        status = "NORMAL"
        if min_val is not None and max_val is not None and not meta.get("cumulative", False):
            if val < min_val or val > max_val:
                span = max_val - min_val if max_val != min_val else 1.0
                ratio = (val - max_val) / span if val > max_val else (min_val - val) / span
                status = "CRITICAL" if ratio >= 0.10 else "WARNING"

        tag_items.append(
            TagLiveItem(
                tag=row.tag,
                value=round(val, 2),
                unit=meta.get("unit", ""),
                equipment=meta.get("equipment", "General Plant"),
                min=min_val,
                max=max_val,
                status=status,
                ts=row.ts or now,
            )
        )

    return LiveResponse(ts=now, tags=tag_items)
