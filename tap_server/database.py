"""
Legacy tap_server.database shim
Delegates to services.tap_server.database
"""
from services.tap_server.database import engine, TapSessionLocal, TapBase, get_tap_db, database_url

__all__ = ["engine", "TapSessionLocal", "TapBase", "get_tap_db", "database_url"]
