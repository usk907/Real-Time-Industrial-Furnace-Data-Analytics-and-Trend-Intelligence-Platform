"""
Legacy tap_server.config shim
Delegates to services.tap_server.config
"""
from services.tap_server.config import TapSettings, tap_settings

__all__ = ["TapSettings", "tap_settings"]
