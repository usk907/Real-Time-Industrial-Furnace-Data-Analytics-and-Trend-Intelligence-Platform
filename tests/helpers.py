"""
Shared Test & Diagnostic Utilities
Provides centralized URLs, auth tokens, session providers, and request helpers.
"""
import os
import requests
from datetime import datetime, timezone, timedelta

# Default test credentials and tokens
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJBZG1pbiIsImV4cCI6MTc5MDE3MjcxM30.wyTOGPz7-la7tcasQBUonkxB3Cd2baXPVjxEe_6hLXA'
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Base URLs configurable via environment variables
BACKEND_BASE_URL = os.getenv("TEST_BACKEND_URL", "http://127.0.0.1:8000")
TAP_BASE_URL = os.getenv("TEST_TAP_URL", "http://127.0.0.1:8001")
WS_URL = os.getenv("TEST_WS_URL", "ws://127.0.0.1:8000/api/ws")

def get_test_session():
    """Returns a requests Session pre-configured with headers and timeouts."""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session

def generate_sample_telemetry_batch():
    """Generates standard telemetry records for TAP testing."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        {
            "timestamp": now_iso,
            "sensor_id": 1,
            "sensor_name": "CB5214 kW",
            "plant": "Gary Steel Works",
            "unit": "kW",
            "value": 22890.5,
            "quality": "GOOD",
            "status": "OK"
        },
        {
            "timestamp": now_iso,
            "sensor_id": 41,
            "sensor_name": "30MW TG-2 kW",
            "plant": "Gary Steel Works",
            "unit": "kW",
            "value": 29210.0,
            "quality": "GOOD",
            "status": "OK"
        },
        {
            "timestamp": now_iso,
            "sensor_id": 51,
            "sensor_name": "SMS-1 Furnace Temp",
            "plant": "Gary Steel Works",
            "unit": "°C",
            "value": 1582.4,
            "quality": "GOOD",
            "status": "OK"
        }
    ]
