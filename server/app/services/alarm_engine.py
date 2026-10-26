"""
Background Alarm Monitoring Engine
Continuously evaluates furnace_latest readings against tag boundaries.
Logs new alarms on threshold breach and resolves them upon return to normal.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from server.app.database import SessionLocal
from server.app.models import Alarm, FurnaceLatest

TAG_META_PATH = Path(__file__).resolve().parent.parent / "tag_meta.json"


class AlarmEngine:
    def __init__(self):
        self.active_alarms = {}  # {tag_name: alarm_id}
        self.tag_meta = {}
        self.load_metadata()

    def load_metadata(self):
        """Loads tag boundaries (min, max) from tag_meta.json."""
        if TAG_META_PATH.exists():
            with open(TAG_META_PATH, "r", encoding="utf-8") as f:
                tags = json.load(f)
                self.tag_meta = {t["name"]: t for t in tags}

    def init_active_alarms_from_db(self, db: Session):
        """Restores in-flight active alarms from the database on startup."""
        try:
            unresolved = db.query(Alarm).filter(Alarm.resolved_at.is_(None)).all()
            for al in unresolved:
                self.active_alarms[al.tag] = al.id
            if unresolved:
                print(
                    f"[ALARM ENGINE]: Restored {len(unresolved)} active unresolved alarms from database."
                )
        except Exception as e:
            print(f"[ALARM ENGINE WARNING]: Could not restore active alarms from DB: {e}")

    def evaluate_readings(self, db: Session):
        """Single tick evaluation of all latest furnace values against tag thresholds."""
        if not self.tag_meta:
            self.load_metadata()

        latest_rows = db.query(FurnaceLatest).all()
        now = datetime.now()

        for row in latest_rows:
            meta = self.tag_meta.get(row.tag)
            if not meta or meta.get("cumulative", False):
                continue

            min_val = meta.get("min")
            max_val = meta.get("max")
            if min_val is None or max_val is None:
                continue

            val = row.value
            is_breached = val < min_val or val > max_val

            if is_breached:
                if row.tag not in self.active_alarms:
                    # New alarm breach
                    if val > max_val:
                        threshold = max_val
                        span = max_val - min_val if max_val != min_val else 1.0
                        ratio = (val - max_val) / span
                    else:
                        threshold = min_val
                        span = max_val - min_val if max_val != min_val else 1.0
                        ratio = (min_val - val) / span

                    severity = "CRITICAL" if ratio >= 0.10 else "WARNING"

                    new_alarm = Alarm(
                        ts=row.ts or now,
                        tag=row.tag,
                        value=round(val, 2),
                        threshold=round(threshold, 2),
                        severity=severity,
                        acknowledged=False,
                    )
                    db.add(new_alarm)
                    db.commit()
                    db.refresh(new_alarm)
                    self.active_alarms[row.tag] = new_alarm.id
                    print(
                        f"[{now.strftime('%H:%M:%S')}] [ALARM TRIGGERED] {row.tag}: {val} (Threshold: {threshold}, Severity: {severity})"
                    )
            else:
                # Value is within normal range
                if row.tag in self.active_alarms:
                    # Alarm condition has resolved
                    alarm_id = self.active_alarms.pop(row.tag)
                    existing_alarm = db.query(Alarm).filter(Alarm.id == alarm_id).first()
                    if existing_alarm:
                        existing_alarm.resolved_at = now
                        db.commit()
                        print(
                            f"[{now.strftime('%H:%M:%S')}] [ALARM RESOLVED] {row.tag} returned to normal ({val}). Alarm #{alarm_id} closed."
                        )

    async def run_loop(self):
        """Asynchronous background worker polling every second."""
        print("[ALARM ENGINE]: Starting background alarm supervisor task...")
        # Initial sync with database
        db = SessionLocal()
        try:
            self.init_active_alarms_from_db(db)
        finally:
            db.close()

        while True:
            try:
                db = SessionLocal()
                try:
                    self.evaluate_readings(db)
                finally:
                    db.close()
            except Exception as e:
                print(f"[ALARM ENGINE ERROR]: {e}")

            await asyncio.sleep(1.0)


alarm_engine = AlarmEngine()
