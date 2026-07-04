import sqlite3
import os
from urllib.parse import urlparse, unquote

def load_db_url():
    # Load DATABASE_URL from .env file
    env_path = ".env"
    if not os.path.exists(env_path):
        return None
    with open(env_path, "r") as f:
        for line in f:
            if line.strip().startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip()
    return None

def inspect_db():
    database_url = load_db_url()
    
    is_mysql = database_url and "mysql" in database_url
    conn = None

    print("=" * 60)
    print("        INDUSTRIAL ENERGY PLATFORM - DATABASE INSPECTOR")
    print("=" * 60)

    try:
        if is_mysql:
            import pymysql
            print(f"[INSPECTOR]: Connecting to MySQL Database...")
            # Parse connection URL: mysql+pymysql://user:password@host:port/database_name
            clean_url = database_url.replace("mysql+pymysql://", "http://").replace("mysql://", "http://")
            u = urlparse(clean_url)
            password = unquote(u.password) if u.password else None
            db_name = u.path.lstrip('/')
            
            conn = pymysql.connect(
                host=u.hostname or '127.0.0.1',
                port=u.port or 3306,
                user=u.username,
                password=password,
                database=db_name
            )
        else:
            db_path = "furnace.db"
            print(f"[INSPECTOR]: Connecting to local SQLite Database ({db_path})...")
            if not os.path.exists(db_path):
                print(f"Error: Database file '{db_path}' not found.")
                return
            conn = sqlite3.connect(db_path)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    cursor = conn.cursor()

    try:
        # 1. Fetch all tables
        if is_mysql:
            cursor.execute("SHOW TABLES;")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            
        tables = [t[0] for t in cursor.fetchall()]
        print(f"\nTables compiled in database:\n   {', '.join(tables)}")
        print("-" * 60)

        # 2. Count records in each table
        print("\nTable Statistics:")
        for table in sorted(tables):
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"   * {table:<25} : {count} records")
            except Exception as e:
                print(f"   * {table:<25} : Error ({e})")
        print("-" * 60)

        # 3. Print active alarms if any
        print("\nActive Alarms:")
        try:
            cursor.execute("SELECT id, time, sensor_id, alarm_type, severity, trigger_value, status FROM alarms WHERE status = 'ACTIVE' ORDER BY time DESC LIMIT 5;")
            alarms = cursor.fetchall()
            if not alarms:
                print("   (No active alarms at this time)")
            for a in alarms:
                print(f"   [ID: {a[0]}] {a[1]} | Sensor ID: {a[2]} | {a[3]} ({a[4]}) | Value: {a[5]}")
        except Exception as e:
            print(f"   Error fetching alarms: {e}")
        print("-" * 60)

        # 4. Print latest telemetry readings
        print("\nLatest Ingested Telemetry Readings (Last 5):")
        try:
            cursor.execute("SELECT time, sensor_id, value, quality, status FROM sensor_readings ORDER BY time DESC, sensor_id ASC LIMIT 5;")
            readings = cursor.fetchall()
            for r in readings:
                print(f"   [{r[0]}] Sensor {r[1]:<2} -> Value: {r[2]:<10} | Quality: {r[3]} | Status: {r[4]}")
            if not readings:
                print("   (No telemetry readings ingested yet)")
        except Exception as e:
            print(f"   Error fetching readings: {e}")
        print("=" * 60)

    finally:
        conn.close()

if __name__ == "__main__":
    inspect_db()
