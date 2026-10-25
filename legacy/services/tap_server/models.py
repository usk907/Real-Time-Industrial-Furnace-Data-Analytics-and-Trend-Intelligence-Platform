"""
TAP Ingestion Server Models
Unifies data model definitions by re-exporting TapTelemetryReading and SensorReading
directly from backend.app.models to ensure synchronized schema metadata across services.
"""
from backend.app.models import TapTelemetryReading, SensorReading
try:
    from services.tap_server.database import TapBase
except ImportError:
    from tap_server.database import TapBase

__all__ = ["TapTelemetryReading", "SensorReading", "TapBase"]
