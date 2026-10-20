import time
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from tap_server.config import tap_settings
from tap_server.database import engine, TapSessionLocal, get_tap_db, TapBase
from tap_server.models import TapTelemetryReading, SensorReading

# Initialize tables
try:
    TapBase.metadata.create_all(bind=engine)
    print("[TAP SERVER]: SQL database schema verified and initialized.")
except Exception as e:
    print(f"[TAP SERVER WARNING]: Failed to auto-create tables: {e}")

app = FastAPI(
    title="IEIP SCADA TAP Server",
    description="Dedicated High-Throughput Industrial Ingestion & SQL Server Tap Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ingestion telemetry metrics tracker
metrics = {
    "server_start_time": datetime.now(timezone.utc).isoformat(),
    "total_batches_received": 0,
    "total_records_ingested": 0,
    "last_batch_timestamp": None,
    "last_batch_records": 0,
    "last_write_latency_ms": 0.0,
    "active_sensors": set()
}

class RawTelemetryItem(BaseModel):
    timestamp: datetime
    sensor_id: int
    sensor_name: str
    plant: Optional[str] = "Gary Steel Works"
    unit: Optional[str] = ""
    value: float
    quality: Optional[str] = "GOOD"
    status: Optional[str] = "OK"

@app.get("/health")
@app.get("/tap/health")
def health_check(db: Session = Depends(get_tap_db)):
    """Health check for TAP Server and its connected SQL Database."""
    try:
        total_sql_records = db.query(func.count(TapTelemetryReading.id)).scalar() or 0
    except Exception:
        total_sql_records = metrics["total_records_ingested"]

    return {
        "status": "ONLINE",
        "service": "IEIP TAP Ingestion Server",
        "port": tap_settings.TAP_SERVER_PORT,
        "database_target": "SQL Server",
        "database_url_type": "MySQL/TiDB" if "mysql" in tap_settings.TAP_DATABASE_URL else "SQLite (tap_data.db)",
        "total_records_in_sql": total_sql_records,
        "active_sensor_count": len(metrics["active_sensors"]),
        "uptime_since": metrics["server_start_time"]
    }

@app.get("/tap/stats")
def get_tap_statistics():
    """Returns real-time data ingestion and SQL write metrics."""
    return {
        "total_batches_received": metrics["total_batches_received"],
        "total_records_ingested": metrics["total_records_ingested"],
        "last_batch_timestamp": metrics["last_batch_timestamp"],
        "last_batch_records": metrics["last_batch_records"],
        "last_write_latency_ms": metrics["last_write_latency_ms"],
        "active_sensor_ids": sorted(list(metrics["active_sensors"]))
    }

@app.post("/tap/telemetry", status_code=status.HTTP_201_CREATED)
@app.post("/api/readings/bulk", status_code=status.HTTP_201_CREATED)
def ingest_telemetry_to_sql(payload: List[RawTelemetryItem], db: Session = Depends(get_tap_db)):
    """
    Ingests live SCADA telemetry stream from simulator / PLC,
    buffers, and commits directly into the SQL Server.
    """
    if not payload:
        return {"status": "ok", "records_inserted": 0}

    start_time = time.time()
    batch_ts = payload[0].timestamp

    tap_records = []
    sensor_records = []
    
    for item in payload:
        metrics["active_sensors"].add(item.sensor_id)
        
        tap_records.append(
            TapTelemetryReading(
                time=item.timestamp,
                sensor_id=item.sensor_id,
                sensor_name=item.sensor_name,
                plant=item.plant,
                unit=item.unit,
                value=item.value,
                quality=item.quality,
                status=item.status
            )
        )
        sensor_records.append(
            SensorReading(
                time=item.timestamp,
                sensor_id=item.sensor_id,
                value=item.value,
                quality=item.quality,
                status=item.status
            )
        )

    try:
        # Write batch to SQL Server
        db.add_all(tap_records)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[TAP SERVER SQL ERROR]: Failed to write batch to SQL: {e}")
        raise HTTPException(status_code=500, detail=f"SQL write error: {e}")

    write_latency = round((time.time() - start_time) * 1000, 2)
    metrics["total_batches_received"] += 1
    metrics["total_records_ingested"] += len(payload)
    metrics["last_batch_timestamp"] = batch_ts.isoformat()
    metrics["last_batch_records"] = len(payload)
    metrics["last_write_latency_ms"] = write_latency

    return {
        "status": "success",
        "tap_server": "ONLINE",
        "sql_records_inserted": len(payload),
        "write_latency_ms": write_latency,
        "timestamp": batch_ts.isoformat()
    }

@app.get("/tap/readings/latest")
def get_latest_readings_from_sql(db: Session = Depends(get_tap_db)):
    """Fetch the latest reading for each sensor directly from the SQL database."""
    recent_readings = db.query(TapTelemetryReading).order_by(desc(TapTelemetryReading.time)).limit(120).all()
    latest_by_sensor = {}
    for r in recent_readings:
        if r.sensor_id not in latest_by_sensor:
            latest_by_sensor[r.sensor_id] = {
                "sensor_id": r.sensor_id,
                "sensor_name": r.sensor_name,
                "plant": r.plant,
                "unit": r.unit,
                "value": r.value,
                "quality": r.quality,
                "status": r.status,
                "time": r.time.isoformat() if r.time else None
            }
    return latest_by_sensor

@app.get("/tap/readings/history")
def get_sensor_history_from_sql(sensor_id: int, limit: int = 100, db: Session = Depends(get_tap_db)):
    """Fetch historical telemetry series directly from the SQL Server."""
    readings = db.query(TapTelemetryReading).filter(
        TapTelemetryReading.sensor_id == sensor_id
    ).order_by(desc(TapTelemetryReading.time)).limit(limit).all()
    
    return [
        {
            "time": r.time.isoformat() if r.time else None,
            "sensor_id": r.sensor_id,
            "sensor_name": r.sensor_name,
            "value": r.value,
            "unit": r.unit,
            "quality": r.quality,
            "status": r.status
        }
        for r in reversed(readings)
    ]
