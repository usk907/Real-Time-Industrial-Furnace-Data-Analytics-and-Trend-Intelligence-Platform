"""
IEIP KPI Calculation & Anomaly Detection Engine
Extracts numerical algorithms, rolling KPI calculations, threshold checks, and linear regression forecasts.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from backend.app.models import (
    AuditLog,
    Notification,
    SystemSetting,
    Alarm,
    KPIHistory,
    Prediction,
    SensorReading
)
from backend.app.schemas import RawTelemetryRecord

# Cache for detecting stuck / frozen sensor signals
frozen_detection_cache: Dict[int, List[float]] = {}


def log_audit(
    db: Session,
    action: str,
    details: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None
) -> None:
    """Logs an administrative or operational action to the audit trail."""
    try:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        print(f"[AUDIT LOG ERROR]: {e}")


def add_notification(
    db: Session,
    user_id: int,
    message: str,
    note_type: str = "INFO"
) -> None:
    """Dispatches a notification to a specific user inbox."""
    try:
        notification = Notification(
            user_id=user_id,
            message=message,
            type=note_type,
            read=False
        )
        db.add(notification)
        db.commit()
    except Exception as e:
        print(f"[NOTIFICATION ERROR]: {e}")


def get_db_setting(db: Session, key: str, default: float) -> float:
    """Fetches an active numeric configuration threshold from the settings table."""
    try:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting and setting.value is not None:
            return float(setting.value)
    except Exception:
        pass
    return default


def check_and_trigger_alarms(
    record: RawTelemetryRecord,
    breaker_limit: float,
    tg_limit: float,
    sms_limit: float,
    active_alarms_map: dict,
    user_ids: list,
    db: Session
) -> None:
    """Evaluates threshold limits on incoming telemetry records and creates/clears alarms."""
    alarm_type = None
    severity = "WARNING"
    val = record.value
    s_id = record.sensor_id

    # Alarm logic rules
    # 1. CB Breaker Overload
    if record.sensor_name in ["CB5214 kW", "CB14 kW"] and val > breaker_limit:
        alarm_type = "CB_OVERLOAD"
        severity = "CRITICAL"
    # 2. Turbine Generator Overload
    elif record.sensor_name in ["30MW TG-2 kW", "33MW TG-3 kW"] and val > tg_limit:
        alarm_type = "TURBINE_OVERLOAD"
        severity = "CRITICAL"
    # 3. SMS Load Surge
    elif record.sensor_name == "SMS Run. Power" and val > sms_limit:
        alarm_type = "SMS_LIMIT_SURGE"
        severity = "WARNING"
    # 4. Low Power Factor Anomaly
    elif record.sensor_name == "Avg. P.F." and val < 0.90:
        alarm_type = "POWER_FACTOR_LOW"
        severity = "WARNING"

    if alarm_type:
        active_alarm = active_alarms_map.get(s_id)
        if not active_alarm or active_alarm.alarm_type != alarm_type:
            new_alarm = Alarm(
                time=record.timestamp,
                sensor_id=s_id,
                alarm_type=alarm_type,
                severity=severity,
                trigger_value=val,
                status="ACTIVE",
                comments=f"Auto-triggered: Value {val} exceeded configured threshold limit."
            )
            db.add(new_alarm)
            active_alarms_map[s_id] = new_alarm
            for u_id in user_ids:
                add_notification(
                    db,
                    u_id,
                    f"Alarm {alarm_type} ({severity}) triggered on device {record.sensor_name}. Value: {val}",
                    "ALARM"
                )
    else:
        # Auto clear alarm state when returned to normal
        active_alarm = active_alarms_map.get(s_id)
        if active_alarm:
            if ((active_alarm.alarm_type == "CB_OVERLOAD" and val <= breaker_limit) or
                (active_alarm.alarm_type == "TURBINE_OVERLOAD" and val <= tg_limit) or
                (active_alarm.alarm_type == "SMS_LIMIT_SURGE" and val <= sms_limit) or
                (active_alarm.alarm_type == "POWER_FACTOR_LOW" and val >= 0.90)):
                active_alarm.status = "CLEARED"
                active_alarm.end_time = record.timestamp
                db.add(active_alarm)
                active_alarms_map.pop(s_id, None)


def check_frozen_sensor(
    record: RawTelemetryRecord,
    active_alarms_map: dict,
    db: Session,
    cache: Optional[Dict[int, List[float]]] = None
) -> None:
    """Detects whether a sensor's readings have remained identical across 10 sample periods."""
    target_cache = cache if cache is not None else frozen_detection_cache
    s_id = record.sensor_id
    if s_id not in target_cache:
        target_cache[s_id] = []

    dev_cache = target_cache[s_id]
    dev_cache.append(record.value)
    if len(dev_cache) > 10:
        dev_cache.pop(0)

    if len(dev_cache) == 10 and len(set(dev_cache)) == 1:
        active_alarm = active_alarms_map.get(s_id)
        if not active_alarm or active_alarm.alarm_type != "FROZEN_SENSOR":
            new_alarm = Alarm(
                time=record.timestamp,
                sensor_id=s_id,
                alarm_type="FROZEN_SENSOR",
                severity="WARNING",
                trigger_value=record.value,
                status="ACTIVE",
                comments="Sensor value frozen static for 10 periods."
            )
            db.add(new_alarm)
            active_alarms_map[s_id] = new_alarm


def calculate_kpis(timestamp: datetime, db: Session) -> None:
    """Computes rolling 5-minute average, peak, and load factors for critical equipment."""
    if timestamp.second != 0:
        return

    # Calculate load factors for equipment running power
    for eq_id, s_id in [(2, 19), (4, 22)]:
        five_min_ago = timestamp - timedelta(minutes=5)
        readings = db.query(SensorReading.value).filter(
            SensorReading.sensor_id == s_id,
            SensorReading.time >= five_min_ago
        ).all()

        if not readings:
            continue

        values = [r[0] for r in readings]
        avg_val = float(np.mean(values))
        peak_val = float(np.max(values))

        load_factor = (avg_val / peak_val) if peak_val > 0 else 1.0

        db.add(KPIHistory(time=timestamp, equipment_id=eq_id, kpi_name="Average Load", value=avg_val, unit="kW"))
        db.add(KPIHistory(time=timestamp, equipment_id=eq_id, kpi_name="Peak Load", value=peak_val, unit="kW"))
        db.add(KPIHistory(time=timestamp, equipment_id=eq_id, kpi_name="Load Factor", value=load_factor, unit=""))
    db.commit()


def compute_moving_regression_forecast(timestamp: datetime, db: Session) -> None:
    """Computes linear trend forecast for 5m, 15m, and 60m horizons on power sensors."""
    if timestamp.second % 10 != 0:
        return

    for sensor_id in [41, 42]:
        five_min_ago = timestamp - timedelta(minutes=5)
        readings = db.query(SensorReading.time, SensorReading.value).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.time >= five_min_ago
        ).order_by(SensorReading.time.asc()).all()

        if len(readings) < 10:
            continue

        times = [float((r[0] - readings[0][0]).total_seconds()) for r in readings]
        values = [float(r[1]) for r in readings]

        slope, intercept = np.polyfit(times, values, 1)

        for horizon in [5, 15, 60]:
            delta_seconds = horizon * 60.0
            predicted_value = max(0.0, float(slope * (times[-1] + delta_seconds) + intercept))
            upper = float(predicted_value + (20.0 * np.sqrt(horizon)))
            lower = max(0.0, float(predicted_value - (20.0 * np.sqrt(horizon))))

            pred = db.query(Prediction).filter(
                Prediction.time == timestamp,
                Prediction.prediction_horizon_minutes == horizon,
                Prediction.sensor_id == sensor_id
            ).first()

            if not pred:
                pred = Prediction(
                    time=timestamp,
                    prediction_horizon_minutes=horizon,
                    sensor_id=sensor_id,
                    predicted_value=predicted_value,
                    upper_bound=upper,
                    lower_bound=lower
                )
            else:
                pred.predicted_value = predicted_value
                pred.upper_bound = upper
                pred.lower_bound = lower
            db.add(pred)

    db.commit()
