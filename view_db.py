import sqlite3
import os
import sys
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

def get_db_connection():
    """Unified database connection provider for MySQL, TiDB, and SQLite."""
    database_url = load_db_url()
    is_mysql = database_url and ("mysql" in database_url or "tidb" in database_url)

    if is_mysql:
        import pymysql
        clean_url = database_url.replace("mysql+pymysql://", "http://").replace("mysql://", "http://")
        u = urlparse(clean_url)
        password = unquote(u.password) if u.password else None
        db_name = u.path.lstrip('/')
        
        return pymysql.connect(
            host=u.hostname or '127.0.0.1',
            port=u.port or 3306,
            user=u.username,
            password=password,
            database=db_name,
            connect_timeout=10
        ), "MySQL"
    else:
        db_path = "furnace.db"
        if not os.path.exists(db_path):
            return None, f"Database file '{db_path}' not found."
        return sqlite3.connect(db_path), "SQLite"

def execute_query(query: str):
    """Executes an arbitrary SQL query and prints a formatted tabular output."""
    conn, engine_type = get_db_connection()
    if not conn:
        print(f"[ERROR]: {engine_type}")
        return

    print("=" * 70)
    print(f" SQL EXECUTION [{engine_type}]")
    print(f" Query: {query}")
    print("=" * 70)

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        
        if cursor.description:
            headers = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            widths = [len(h) for h in headers]
            for row in rows:
                for i, val in enumerate(row):
                    widths[i] = max(widths[i], len(str(val)))
                    
            header_str = " | ".join(f"{h:<{widths[i]}}" for i, h in enumerate(headers))
            separator = "-+-".join("-" * widths[i] for i in range(len(headers)))
            
            print(header_str)
            print(separator)
            
            for row in rows:
                print(" | ".join(f"{str(val):<{widths[i]}}" for i, val in enumerate(row)))
                
            print(f"\n({len(rows)} row(s) returned)\n")
        else:
            conn.commit()
            print(f"\n[SUCCESS]: Query executed successfully ({cursor.rowcount} row(s) affected).\n")
    except Exception as e:
        print(f"[QUERY ERROR]: {e}")
    finally:
        conn.close()

def inspect_db():
    """Inspects the database schema, table statistics, alarms, and recent telemetry."""
    conn, engine_type = get_db_connection()
    if not conn:
        print(f"[ERROR]: {engine_type}")
        return

    print("=" * 60)
    print(f"   INDUSTRIAL ENERGY PLATFORM - DATABASE INSPECTOR [{engine_type}]")
    print("=" * 60)

    cursor = conn.cursor()

    try:
        # 1. Fetch all tables
        if engine_type == "MySQL":
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
    if len(sys.argv) > 1:
        raw_arg = " ".join(sys.argv[1:])
        if raw_arg.startswith("--query="):
            execute_query(raw_arg.split("=", 1)[1])
        elif raw_arg == "--inspect":
            inspect_db()
        else:
            execute_query(raw_arg)
    else:
        inspect_db()
