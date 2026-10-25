"""
Legacy tap_server.models shim
Delegates to services.tap_server.models
"""
from services.tap_server.models import TapTelemetryReading, SensorReading, TapBase

__all__ = ["TapTelemetryReading", "SensorReading", "TapBase"]
