from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import numpy as np
import os
import csv
from typing import List, Dict, Optional

from backend.app.database import get_db
from backend.app.auth import create_access_token, verify_password, get_current_user
from backend.app.models import User, Role, Sensor, SensorReading, Alarm, Equipment, KPIHistory, Prediction, Report
from backend.app.schemas import UserLogin, Token, RawTelemetryRecord, SensorOut, AlarmOut, AlarmAcknowledge, ReportOut
from backend.app.websocket_manager import ws_manager

router = APIRouter()

# Global limits config
SETTINGS_STORE = {
    "sampling_interval_seconds": 1,
    "alarm_threshold_breaker_max": 45000.0,
    "alarm_threshold_tg_max": 30000.0,
    "alarm_threshold_sms_max": 95000.0,
    "prediction_horizon_minutes": 60
}

# Stuck/frozen sensor tracking
frozen_detection_cache: Dict[int, List[float]] = {}

# -----------------------------------------------------
# AUTHENTICATION
# -----------------------------------------------------
@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    role = db.query(Role).filter(Role.id == user.role_id).first()
    permissions = role.permissions if role else []
    
    token_data = {"sub": user.username, "role": role.name if role else "Viewer"}
    access_token = create_access_token(data=token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role.name if role else "Viewer",
        "permissions": permissions
    }

# -----------------------------------------------------
# BULK TELEMETRY INGESTION PIPELINE
# -----------------------------------------------------
@router.post("/readings/bulk", status_code=status.HTTP_201_CREATED)
async def ingest_bulk_telemetry(payload: List[RawTelemetryRecord], db: Session = Depends(get_db)):
    if not payload:
        return {"status": "ok", "records_inserted": 0}

    timestamp = payload[0].timestamp
    broadcast_data = {
        "event": "TELEMETRY_UPDATE",
        "timestamp": timestamp.isoformat(),
        "readings": {}
    }

    # Process and validate each reading
    for record in payload:
        # Anomaly checks
        check_and_trigger_alarms(record, db)
        check_frozen_sensor(record, db)

        # DB Insertion
        reading = SensorReading(
            time=record.timestamp,
            sensor_id=record.sensor_id,
            value=record.value,
            quality=record.quality,
            status=record.status
        )
        db.add(reading)
        
        # Format live broadcast payload
        broadcast_data["readings"][record.sensor_id] = {
            "name": record.sensor_name,
            "value": record.value,
            "unit": record.unit,
            "status": record.status,
            "equipment": record.equipment
        }
        
    db.commit()

    # Dynamic KPI execution
    try:
        calculate_kpis(timestamp, db)
    except Exception as kpi_err:
        print(f"[KPI ERROR]: {kpi_err}")

    # Forecast execution (predict TG outputs - sensor IDs 41 and 42)
    try:
        compute_moving_regression_forecast(timestamp, db)
    except Exception as fc_err:
        print(f"[FORECAST ERROR]: {fc_err}")

    # WebSocket Broadcast
    await ws_manager.broadcast(broadcast_data)
    
    return {
        "status": "success",
        "records_inserted": len(payload),
        "timestamp": timestamp
    }

def check_and_trigger_alarms(record: RawTelemetryRecord, db: Session):
    alarm_type = None
    severity = "WARNING"
    val = record.value

    # Overload warnings mapping to screenshots
    if record.sensor_name == "CB5214 kW" and val > SETTINGS_STORE["alarm_threshold_breaker_max"]:
        alarm_type = "CB_OVERLOAD"
        severity = "CRITICAL"
    elif record.sensor_name == "30MW TG-2 kW" and val > SETTINGS_STORE["alarm_threshold_tg_max"]:
        alarm_type = "TURBINE_OVERLOAD"
        severity = "CRITICAL"
    elif record.sensor_name == "SMS Run. Power" and val > SETTINGS_STORE["alarm_threshold_sms_max"]:
        alarm_type = "SMS_LIMIT_SURGE"
        severity = "WARNING"

    if alarm_type:
        active_alarm = db.query(Alarm).filter(
            Alarm.sensor_id == record.sensor_id,
            Alarm.alarm_type == alarm_type,
            Alarm.status == "ACTIVE"
        ).first()
        
        if not active_alarm:
            new_alarm = Alarm(
                time=record.timestamp,
                sensor_id=record.sensor_id,
                alarm_type=alarm_type,
                severity=severity,
                trigger_value=val,
                status="ACTIVE",
                comments=f"Auto-triggered: Value {val} exceeded limits."
            )
            db.add(new_alarm)
            print(f"[ANOMALY]: Registered alert {alarm_type} on sensor {record.sensor_id}")
    else:
        # Auto clear when returned to normal
        active_alarms = db.query(Alarm).filter(
            Alarm.sensor_id == record.sensor_id,
            Alarm.status == "ACTIVE"
        ).all()
        for alarm in active_alarms:
            if (alarm.alarm_type == "CB_OVERLOAD" and val <= SETTINGS_STORE["alarm_threshold_breaker_max"]) or \
               (alarm.alarm_type == "TURBINE_OVERLOAD" and val <= SETTINGS_STORE["alarm_threshold_tg_max"]) or \
               (alarm.alarm_type == "SMS_LIMIT_SURGE" and val <= SETTINGS_STORE["alarm_threshold_sms_max"]):
                alarm.status = "CLEARED"
                alarm.end_time = record.timestamp
                db.add(alarm)

def check_frozen_sensor(record: RawTelemetryRecord, db: Session):
    s_id = record.sensor_id
    if s_id not in frozen_detection_cache:
        frozen_detection_cache[s_id] = []
        
    cache = frozen_detection_cache[s_id]
    cache.append(record.value)
    if len(cache) > 10:
        cache.pop(0)
        
    if len(cache) == 10 and len(set(cache)) == 1:
        active_alarm = db.query(Alarm).filter(
            Alarm.sensor_id == s_id,
            Alarm.alarm_type == "FROZEN_SENSOR",
            Alarm.status == "ACTIVE"
        ).first()
        
        if not active_alarm:
            new_alarm = Alarm(
                time=record.timestamp,
                sensor_id=s_id,
                alarm_type="FROZEN_SENSOR",
                severity="WARNING",
                trigger_value=record.value,
                status="ACTIVE",
                comments="Sensor value static for 10 periods."
            )
            db.add(new_alarm)

def calculate_kpis(timestamp: datetime, db: Session):
    if timestamp.second != 0:
        return
        
    # Calculate SMS Load Factors (SMS-1: equipment 2, SMS-4: equipment 4)
    for eq_id, s_id in [(2, 19), (4, 22)]:
        five_min_ago = timestamp - timedelta(minutes=5)
        readings = db.query(SensorReading.value).filter(
            SensorReading.sensor_id == s_id,
            SensorReading.time >= five_min_ago
        ).all()
        
        if not readings:
            continue
            
        values = [r[0] for r in readings]
        avg_val = np.mean(values)
        peak_val = np.max(values)
        
        load_factor = (avg_val / peak_val) if peak_val > 0 else 1.0
        
        db.add(KPIHistory(time=timestamp, equipment_id=eq_id, kpi_name="Average Load", value=avg_val, unit="kW"))
        db.add(KPIHistory(time=timestamp, equipment_id=eq_id, kpi_name="Peak Load", value=peak_val, unit="kW"))
        db.add(KPIHistory(time=timestamp, equipment_id=eq_id, kpi_name="Load Factor", value=load_factor, unit=""))

def compute_moving_regression_forecast(timestamp: datetime, db: Session):
    if timestamp.second % 10 != 0:
        return
        
    # Forecast active turbine outputs (TG-2 ID 41, TG-3 ID 42)
    for sensor_id in [41, 42]:
        five_min_ago = timestamp - timedelta(minutes=5)
        readings = db.query(SensorReading.time, SensorReading.value).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.time >= five_min_ago
        ).order_by(SensorReading.time.asc()).all()
        
        if len(readings) < 10:
            continue
            
        times = [float((r[0] - readings[0][0]).total_seconds()) for r in readings]
        values = [r[1] for r in readings]
        
        slope, intercept = np.polyfit(times, values, 1)
        
        for horizon in [5, 15, 60]:
            delta_seconds = horizon * 60.0
            predicted_value = max(0.0, slope * (times[-1] + delta_seconds) + intercept)
            upper = predicted_value + (20.0 * np.sqrt(horizon))
            lower = max(0.0, predicted_value - (20.0 * np.sqrt(horizon)))
            
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

# -----------------------------------------------------
# CORE DASHBOARD API
# -----------------------------------------------------
@router.get("/dashboard")
def get_dashboard_summary(db: Session = Depends(get_db)):
    # 1. Fetch latest reading values for all 50 sensors
    latest_readings = {}
    for s_id in range(1, 51):
        reading = db.query(SensorReading).filter(SensorReading.sensor_id == s_id).order_by(desc(SensorReading.time)).first()
        latest_readings[s_id] = reading.value if reading else 0.0

    # Running Furnace Count calculation from power levels
    running_furnaces = 0
    # SMS-4 furnaces (sensors 25, 29, 33, 37)
    for s_id in [25, 29, 33, 37]:
        if latest_readings.get(s_id, 0.0) > 50.0:
            running_furnaces += 1
            
    # SMS-1 power check
    if latest_readings.get(19, 0.0) > 100.0:
        running_furnaces += 1

    # Grid summaries
    grid_power_combined = latest_readings.get(1, 0.0) + latest_readings.get(2, 0.0)
    generation_combined = latest_readings.get(41, 0.0) + latest_readings.get(42, 0.0)

    # 2. Extract latest alarms
    active_alarms = db.query(Alarm).filter(Alarm.status == "ACTIVE").order_by(desc(Alarm.time)).limit(10).all()
    alarms_out = [
        {
            "id": a.id,
            "time": a.time,
            "sensor_id": a.sensor_id,
            "alarm_type": a.alarm_type,
            "severity": a.severity,
            "trigger_value": a.trigger_value,
            "status": a.status,
            "comments": a.comments
        } for a in active_alarms
    ]

    # 3. Compile KPI values
    kpis = {
        "grid_power_combined": grid_power_combined,
        "generation_combined": generation_combined,
        "cb5214_kw": latest_readings.get(1, 0.0),
        "cb14_kw": latest_readings.get(2, 0.0),
        "cb52g4_kw": latest_readings.get(3, 0.0),
        "sms_allocated_power": latest_readings.get(6, 0.0),
        "sms_run_power": latest_readings.get(7, 0.0),
        "sms_1_run_power": latest_readings.get(19, 0.0),
        "sms_4_run_power": latest_readings.get(22, 0.0),
        "sms_4_utl_pct": latest_readings.get(23, 0.0),
        "running_furnace_count": running_furnaces,
        "avg_pf": latest_readings.get(47, 0.929),
        "load_factor": latest_readings.get(48, 23.279)
    }

    # 4. Extract latest predictions
    predictions = db.query(Prediction).order_by(desc(Prediction.time)).limit(6).all()
    pred_data = [
        {
            "horizon": p.prediction_horizon_minutes,
            "sensor_id": p.sensor_id,
            "predicted": p.predicted_value,
            "upper": p.upper_bound,
            "lower": p.lower_bound
        } for p in predictions
    ]

    return {
        "kpis": kpis,
        "alarms": alarms_out,
        "predictions": pred_data
    }

# -----------------------------------------------------
# DIRECT TELEMETRY HISTORY
# -----------------------------------------------------
@router.get("/sensors", response_model=List[SensorOut])
def list_sensors(db: Session = Depends(get_db)):
    return db.query(Sensor).filter(Sensor.is_active == True).all()

@router.get("/history")
def get_historical_telemetry(
    sensor_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SensorReading)
    if sensor_id:
        query = query.filter(SensorReading.sensor_id == sensor_id)
    if start_time:
        query = query.filter(SensorReading.time >= start_time)
    else:
        query = query.filter(SensorReading.time >= datetime.utcnow() - timedelta(hours=1))
    if end_time:
        query = query.filter(SensorReading.time <= end_time)

    readings = query.order_by(SensorReading.time.asc()).all()
    return [{"time": r.time, "sensor_id": r.sensor_id, "value": r.value, "quality": r.quality} for r in readings]

@router.get("/trends")
def get_statistical_trends(sensor_id: int, db: Session = Depends(get_db)):
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    readings = db.query(SensorReading.value).filter(
        SensorReading.sensor_id == sensor_id,
        SensorReading.time >= one_hour_ago
    ).all()

    if not readings:
        return {"sensor_id": sensor_id, "mean": 0.0, "std_dev": 0.0, "max": 0.0, "min": 0.0, "variance": 0.0}

    values = [r[0] for r in readings]
    return {
        "sensor_id": sensor_id,
        "mean": float(np.mean(values)),
        "std_dev": float(np.std(values)),
        "max": float(np.max(values)),
        "min": float(np.min(values)),
        "median": float(np.median(values)),
        "variance": float(np.var(values))
    }

# -----------------------------------------------------
# ALARMS CONSOLE
# -----------------------------------------------------
@router.get("/alarms", response_model=List[AlarmOut])
def get_alarms(status: Optional[str] = None, severity: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Alarm)
    if status:
        query = query.filter(Alarm.status == status)
    if severity:
        query = query.filter(Alarm.severity == severity)
    return query.order_by(desc(Alarm.time)).all()

@router.put("/alarms/{alarm_id}/acknowledge")
def acknowledge_alarm(alarm_id: int, payload: AlarmAcknowledge, db: Session = Depends(get_db)):
    alarm = db.query(Alarm).filter(Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found.")
        
    alarm.status = "ACKNOWLEDGED"
    alarm.acknowledged_by = payload.acknowledged_by
    alarm.comments = payload.comments
    db.commit()
    return {"status": "success", "alarm_id": alarm_id, "state": "ACKNOWLEDGED"}

# -----------------------------------------------------
# REPORTS BUILD
# -----------------------------------------------------
@router.get("/reports", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_db)):
    return db.query(Report).order_by(desc(Report.created_at)).all()

@router.post("/reports/generate")
def compile_csv_report(report_type: str = "DAILY", format: str = "CSV", db: Session = Depends(get_db)):
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_name = f"scada_furnace_{report_type.lower()}_{timestamp_str}.csv"
    
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, report_name)
    
    readings = db.query(SensorReading).order_by(desc(SensorReading.time)).limit(100).all()
    with open(file_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Timestamp", "Sensor ID", "Value", "Quality", "Status"])
        for r in readings:
            writer.writerow([r.time, r.sensor_id, r.value, r.quality, r.status])
            
    new_report = Report(
        name=report_name,
        report_type=report_type,
        format=format,
        file_path=file_path
    )
    db.add(new_report)
    db.commit()
    return {"status": "success", "report_id": new_report.id, "file_name": report_name}

@router.get("/settings")
def get_system_settings():
    return SETTINGS_STORE

@router.post("/settings")
def update_system_settings(payload: dict):
    for k, v in payload.items():
        if k in SETTINGS_STORE:
            SETTINGS_STORE[k] = v
    return {"status": "success", "updated_settings": SETTINGS_STORE}
