"""
IEIP Data Retention Cleaner
Prunes furnace_readings older than 7 days from the MySQL database.
Can be executed standalone or scheduled via Windows Task Scheduler.
"""
import os
import sys
import pymysql
from datetime import datetime, timedelta

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "admin_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "AdminPassword123!")
DB_NAME = os.getenv("DB_NAME", "furnace_db")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))

def prune_old_readings():
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    print(f"[{datetime.now().isoformat()}] Connecting to {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}...")
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=True
        )
        with conn.cursor() as cursor:
            sql = "DELETE FROM furnace_readings WHERE ts < %s"
            deleted = cursor.execute(sql, (cutoff,))
            print(f"[{datetime.now().isoformat()}] Prune complete: removed {deleted} readings older than {cutoff.isoformat()}.")
        conn.close()
    except Exception as e:
        print(f"[ERROR]: Failed to prune readings: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    prune_old_readings()
