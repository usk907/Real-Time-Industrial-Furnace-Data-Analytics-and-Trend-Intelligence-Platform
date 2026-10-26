"""
Industrial Energy Intelligence Platform (IEIP)
Part 1: Fake Furnace Data Generator

Continuously generates realistic SCADA telemetry for 60 industrial furnace tags
and writes to MySQL tables 'furnace_readings' and 'furnace_latest' in atomic transactions.
"""

import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import pymysql
from dotenv import load_dotenv

# Load local generator environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

from tags import TAGS

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3307"))
DB_USER = os.getenv("DB_USER", "generator_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")
if (
    not DB_PASSWORD
    or "<your_" in DB_PASSWORD.lower()
    or "placeholder" in DB_PASSWORD.lower()
    or "replace_with" in DB_PASSWORD.lower()
):
    raise ValueError(
        "Refusing to start: DB_PASSWORD is missing or set to a placeholder in generator/.env. "
        "Please configure a valid database password."
    )
DB_NAME = os.getenv("DB_NAME", "furnace_db")
GEN_INTERVAL_SECONDS = float(os.getenv("GEN_INTERVAL_SECONDS", "1.0"))
LOG_INTERVAL_TICKS = int(os.getenv("LOG_INTERVAL_TICKS", "10"))


class FurnaceDataGenerator:
    def __init__(self):
        # Initialize internal state per tag with its starting value
        self.state = {tag["name"]: float(tag["start"]) for tag in TAGS}
        self.conn = None
        self.tick_count = 0

    def get_connection(self):
        """Establishes or verifies connection to MySQL with auto-reconnect."""
        while True:
            try:
                if self.conn is not None:
                    try:
                        self.conn.ping(reconnect=True)
                        return self.conn
                    except Exception:
                        self.conn = None

                self.conn = pymysql.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    autocommit=False,
                    charset="utf8mb4",
                    connect_timeout=5,
                )
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connected to MySQL ({DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME})"
                )
                return self.conn
            except Exception as e:
                print(
                    f"[RECONNECT ERROR]: Cannot connect to MySQL at {DB_HOST}:{DB_PORT}. Retrying in 2 seconds... ({e})"
                )
                time.sleep(2.0)

    def load_latest_state(self):
        """Loads last recorded values from furnace_latest so cumulative tags and values persist across restarts."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT tag, value FROM furnace_latest")
                rows = cursor.fetchall()
                loaded = 0
                for tag_name, val in rows:
                    if tag_name in self.state:
                        self.state[tag_name] = float(val)
                        loaded += 1
                if loaded > 0:
                    print(
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Restored {loaded} tag states from furnace_latest (cumulative kWh preserved)."
                    )
                else:
                    print(
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No previous state found in furnace_latest. Initialized with starting values."
                    )
        except Exception as e:
            print(
                f"[STATE WARNING]: Could not load latest values from furnace_latest: {e}. Using default values."
            )

    def advance_state(self):
        """Advances bounded random walks for all 60 tags and handles anomaly injection."""
        self.tick_count += 1
        anomaly_tag = None
        anomaly_val = None

        # Roughly 1 in 500 ticks, inject an alarm breach into a non-cumulative tag
        if self.tick_count % 500 == 0:
            target_candidates = [
                t
                for t in TAGS
                if not t.get("cumulative")
                and ("Temp" in t["name"] or "Power" in t["name"] or "Pressure" in t["name"])
            ]
            if target_candidates:
                chosen = random.choice(target_candidates)
                anomaly_tag = chosen["name"]
                # Spike 18% above nominal max
                anomaly_val = round(chosen["max"] * 1.18, 2)

        for tag in TAGS:
            name = tag["name"]
            current = self.state[name]
            is_cumulative = tag.get("cumulative", False)

            if name == anomaly_tag and anomaly_val is not None:
                self.state[name] = anomaly_val
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [ANOMALY INJECTED] {name} spiked to {anomaly_val} {tag['unit']} (Max: {tag['max']})"
                )
                continue

            if is_cumulative:
                # Cumulative energy only increases
                increment = random.uniform(tag["step"] * 0.8, tag["step"] * 1.2)
                self.state[name] = round(current + increment, 2)
            else:
                # Bounded random walk
                delta = random.uniform(-tag["step"], tag["step"])
                # Add gentle mean reversion toward midpoint
                midpoint = (tag["min"] + tag["max"]) / 2.0
                reversion = (midpoint - current) * 0.05
                new_val = current + delta + reversion

                # Clamp strictly within normal operational min and max
                clamped = max(tag["min"], min(tag["max"], new_val))
                self.state[name] = round(clamped, 2)

    def generate_tick(self):
        """Generates 1 tick of 60 tag readings and writes to MySQL in one transaction."""
        self.advance_state()
        now = datetime.now()

        # Build batch data for furnace_readings and furnace_latest
        readings_batch = []
        latest_batch = []

        for tag in TAGS:
            name = tag["name"]
            val = self.state[name]
            quality = 1  # 1 = GOOD quality
            readings_batch.append((now, name, val, quality))
            latest_batch.append((name, val, now))

        # Atomic transaction write to MySQL
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Insert time-series historical records
                insert_readings_sql = (
                    "INSERT INTO furnace_readings (ts, tag, value, quality) VALUES (%s, %s, %s, %s)"
                )
                cursor.executemany(insert_readings_sql, readings_batch)

                # 2. Update real-time latest cache table
                replace_latest_sql = (
                    "REPLACE INTO furnace_latest (tag, value, ts) VALUES (%s, %s, %s)"
                )
                cursor.executemany(replace_latest_sql, latest_batch)

            conn.commit()

            if self.tick_count % LOG_INTERVAL_TICKS == 0:
                print(
                    f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Tick #{self.tick_count}: "
                    f"60 tags committed (Readings total +60, Latest updated)."
                )
        except Exception as e:
            conn.rollback()
            print(f"[TRANSACTION ERROR]: Failed to write tick #{self.tick_count}: {e}")
            self.conn = None

    def run(self, max_ticks: int = None):
        """Continuous execution loop."""
        print(
            f"IEIP Furnace Data Generator started. Interval: {GEN_INTERVAL_SECONDS}s, Tags: {len(TAGS)}"
        )
        print("Press Ctrl+C to stop.")
        self.load_latest_state()
        ticks_done = 0
        try:
            while True:
                start_time = time.time()
                self.generate_tick()
                ticks_done += 1

                if max_ticks is not None and ticks_done >= max_ticks:
                    print(f"Completed requested {max_ticks} ticks. Exiting.")
                    break

                elapsed = time.time() - start_time
                sleep_time = max(0.0, GEN_INTERVAL_SECONDS - elapsed)
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\nGenerator stopped by user.")
        finally:
            if self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass


if __name__ == "__main__":
    max_ticks = None
    if len(sys.argv) > 1:
        try:
            max_ticks = int(sys.argv[1])
        except ValueError:
            pass

    generator = FurnaceDataGenerator()
    generator.run(max_ticks=max_ticks)
