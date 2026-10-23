"""
Shared Telemetry Schemas
Used across Backend Ingestion, TAP Ingestion Server, and SCADA Simulator.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RawTelemetryItem(BaseModel):
    """Normalized single sensor telemetry record."""
    timestamp: datetime
    sensor_id: int
    sensor_name: str
    plant: Optional[str] = "Gary Steel Works"
    unit: Optional[str] = ""
    value: float
    quality: Optional[str] = "GOOD"
    status: Optional[str] = "OK"


# Backward-compatible alias
RawTelemetryRecord = RawTelemetryItem
