"""
Integration test for live MySQL database connection on port 3307.
Marked with @pytest.mark.live_db and gracefully skips if MySQL is offline.
"""
import os
import re
import pytest
from pathlib import Path

def get_mysql_credentials():
    """Extracts DB credentials from server/.env, generator/.env or environment."""
    root_dir = Path(__file__).resolve().parent.parent
    server_env = root_dir / "server" / ".env"
    gen_env = root_dir / "generator" / ".env"

    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3307"))
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "furnace_db")

    if server_env.exists() and (not user or not password):
        content = server_env.read_text(encoding="utf-8")
        match = re.search(r"DATABASE_URL=mysql\+pymysql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^\s]+)", content)
        if match:
            user = match.group(1)
            password = match.group(2)
            host = match.group(3)
            port = int(match.group(4)) if match.group(4) else 3307
            database = match.group(5)

    if gen_env.exists() and (not user or not password):
        for line in gen_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DB_USER="):
                user = line.split("=", 1)[1].strip("'\"")
            elif line.startswith("DB_PASSWORD="):
                password = line.split("=", 1)[1].strip("'\"")
            elif line.startswith("DB_PORT="):
                port = int(line.split("=", 1)[1].strip("'\""))

    return host, port, user, password, database

@pytest.mark.live_db
def test_live_mysql_connection():
    """Connects to live MySQL database on port 3307 and verifies table connectivity."""
    try:
        import pymysql
    except ImportError:
        pytest.skip("pymysql is not installed in current test environment")

    host, port, user, password, database = get_mysql_credentials()

    if not password:
        pytest.skip("No MySQL database credentials configured in server/.env or generator/.env")

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=2
        )
    except Exception as exc:
        pytest.skip(f"Live MySQL database offline on {host}:{port}: {exc}")

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS probe;")
            row = cursor.fetchone()
            assert row[0] == 1, "Expected SELECT 1 query probe to return 1"

            cursor.execute("SHOW TABLES;")
            tables = [r[0] for r in cursor.fetchall()]
            assert "furnace_latest" in tables, "Expected 'furnace_latest' table to exist in furnace_db"
            assert "furnace_readings" in tables, "Expected 'furnace_readings' table to exist in furnace_db"
    finally:
        conn.close()
