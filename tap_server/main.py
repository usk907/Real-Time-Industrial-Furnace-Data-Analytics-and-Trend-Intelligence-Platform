"""
Legacy tap_server.main shim
Re-exports FastAPI app and handlers from services.tap_server.main
"""
from services.tap_server.main import (
    app,
    metrics,
    RawTelemetryItem,
    health_check,
    get_tap_statistics,
    ingest_telemetry_to_sql,
    get_latest_readings_from_sql,
    get_sensor_history_from_sql
)

__all__ = [
    "app",
    "metrics",
    "RawTelemetryItem",
    "health_check",
    "get_tap_statistics",
    "ingest_telemetry_to_sql",
    "get_latest_readings_from_sql",
    "get_sensor_history_from_sql"
]
