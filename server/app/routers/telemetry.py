"""
IEIP Telemetry Ingestion, Historical Trends & TAP Bridge Router
Endpoints:
  - POST /readings/bulk
  - GET  /trends
  - GET  /tap/status
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import numpy as np
import requests
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import Device, SensorReading
from backend.app.schemas import RawTelemetryRecord
from backend.app.websocket_manager import ws_manager
from backend.app.influx_client import influx_manager

router = APIRouter(tags=["Telemetry & Trends"])


# -----------------------------------------------------
# BULK TELEMETRY INGESTION PIPELINE
# -----------------------------------------------------
@router.post("/readings/bulk", status_code=status.HTTP_201_CREATED)
async def ingest_bulk_telemetry(payload: List[RawTelemetryRecord], db: Session = Depends(get_db)):
    if not payload:
        return {"status": "ok", "records_inserted": 0}

    timestamp = payload[0].timestamp
    broadcast_data = {
        "event": "TELEMETRY_UPDATE",
        "timestamp": timestamp.isoformat(),
        "readings": {
            r.sensor_id: {
                "name": r.sensor_name,
                "value": r.value,
                "unit": r.unit,
                "status": r.status,
                "quality": r.quality
            }
            for r in payload
        }
    }

    # Broadcast to live UI immediately
    if ws_manager.active_connections:
        await ws_manager.broadcast(broadcast_data)

    def _sync_db_write():
        try:
            readings = [
                SensorReading(
                    time=r.timestamp,
                    sensor_id=r.sensor_id,
                    value=r.value,
                    quality=r.quality,
                    status=r.status
                )
                for r in payload
            ]
            db.bulk_save_objects(readings)
            db.commit()
        except Exception:
            db.rollback()

    asyncio.create_task(asyncio.to_thread(_sync_db_write))
    return {"status": "success", "records_inserted": len(payload), "timestamp": timestamp}


# -----------------------------------------------------
# ADVANCED TRENDS & COMPARISONS (InfluxDB Integration)
# -----------------------------------------------------
@router.get("/trends")
def get_trends(
    sensor_id: int,
    quick_filter: Optional[str] = "1h",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    resolution: Optional[str] = "1m",
    shift: Optional[str] = None,
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    FILTER_MAP = {
        "1h": (1, "1m"),
        "6h": (6, "1m"),
        "12h": (12, "1m"),
        "24h": (24, "1m"),
        "7d": (168, "15m"),
        "30d": (720, "1h"),
        "90d": (2160, "1d")
    }
    hours, default_res = FILTER_MAP.get(quick_filter, (1, "1m"))

    start_time = (start_time or (now - timedelta(hours=hours))).astimezone(timezone.utc) if start_time else (now - timedelta(hours=hours))
    end_time = (end_time or now).astimezone(timezone.utc) if end_time else now
    resolution = resolution or default_res

    # 1. Query InfluxDB / SQL Fallback
    try:
        readings_list = influx_manager.query_readings(
            sensor_id=sensor_id,
            start_time=start_time,
            end_time=end_time,
            resolution=resolution
        )
    except Exception:
        readings_list = []

    if not readings_list:
        sql_readings = db.query(SensorReading.time, SensorReading.value).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.time >= start_time,
            SensorReading.time <= end_time
        ).order_by(SensorReading.time.asc()).all()
        readings_list = [{"time": r[0], "sensor_id": sensor_id, "value": r[1]} for r in sql_readings]

    # Shift filter
    if shift == "Night":
        readings_list = [r for r in readings_list if r["time"].hour >= 22 or r["time"].hour < 6]
    elif shift in ("Morning", "Afternoon"):
        s_min, s_max = (6, 14) if shift == "Morning" else (14, 22)
        readings_list = [r for r in readings_list if s_min <= r["time"].hour < s_max]

    if not readings_list:
        return {
            "sensor_id": sensor_id,
            "readings": [],
            "statistics": {
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "median": 0.0,
                "std_dev": 0.0,
                "variance": 0.0,
                "total_consumption": 0.0,
                "running_hours": 0.0,
                "downtime_hours": 0.0,
                "efficiency": 0.0
            }
        }

    vals = np.array([r["value"] for r in readings_list], dtype=float)
    total_hours = max((end_time - start_time).total_seconds() / 3600.0, 0.01)

    device = db.query(Device.unit).filter(Device.id == sensor_id).first()
    is_power = device and device[0] == "kW"
    total_consumption = float(vals.mean() * total_hours) if is_power else 0.0

    running_hours = float((vals > 5.0).sum() / len(vals) * total_hours)
    downtime_hours = max(0.0, total_hours - running_hours)
    efficiency = round((running_hours / total_hours) * 100.0, 1)

    return {
        "sensor_id": sensor_id,
        "readings": [{"time": r["time"].isoformat(), "value": r["value"]} for r in readings_list],
        "statistics": {
            "avg": round(float(vals.mean()), 2),
            "min": round(float(vals.min()), 2),
            "max": round(float(vals.max()), 2),
            "median": round(float(np.median(vals)), 2),
            "std_dev": round(float(vals.std()), 2),
            "variance": round(float(vals.var()), 2),
            "total_consumption": round(total_consumption, 2),
            "running_hours": round(running_hours, 2),
            "downtime_hours": round(downtime_hours, 2),
            "efficiency": efficiency
        }
    }


# -----------------------------------------------------
# TAP SERVER INTEGRATION & TELEMETRY MONITORING
# -----------------------------------------------------
@router.get("/tap/status")
def get_tap_server_status(db: Session = Depends(get_db)):
    """Checks the status of the dedicated TAP Server and its SQL Server table storage."""
    tap_url = "http://127.0.0.1:8001/tap/health"
    stats_url = "http://127.0.0.1:8001/tap/stats"

    tap_online = False
    tap_info = {}
    stats = {}

    try:
        r = requests.get(tap_url, timeout=1.0)
        if r.status_code == 200:
            tap_online = True
            tap_info = r.json()
            r_stats = requests.get(stats_url, timeout=1.0)
            if r_stats.status_code == 200:
                stats = r_stats.json()
    except Exception:
        tap_online = False

    total_sql_readings = db.query(func.count(SensorReading.time)).scalar() or 0

    return {
        "tap_server_online": tap_online,
        "tap_server_url": "http://127.0.0.1:8001",
        "sql_database_connected": True,
        "total_sql_readings": total_sql_readings,
        "tap_details": tap_info if tap_online else {
            "status": "OFFLINE",
            "message": "TAP server is not running on port 8001. Using backend direct ingestion fallback."
        },
        "metrics": stats
    }
