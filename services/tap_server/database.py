"""
TAP Ingestion Server Database Connector
Reuses the centralized database connection engine and metadata pool from backend.app.database
while preserving full backward compatibility for get_tap_db, TapSessionLocal, and TapBase.
"""
from backend.app.database import engine, SessionLocal as TapSessionLocal, Base as TapBase, get_db as get_tap_db, database_url

__all__ = ["engine", "TapSessionLocal", "TapBase", "get_tap_db", "database_url"]
