from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta, timezone, time
import numpy as np
import os
import csv
from typing import List, Dict, Any, Optional

from backend.app.database import get_db
from backend.app.auth import create_access_token, verify_password, get_password_hash, get_current_user, RoleChecker, blacklist_token
from backend.app.models import User, Role, Plant, Department, Machine, Device, SensorReading, Alarm, Event, Prediction, KPIHistory, Report, AuditLog, SystemSetting, Notification
from backend.app.schemas import (
    UserLogin, Token, RawTelemetryRecord, ReadingOut, AlarmOut, AlarmAcknowledge, ReportOut,
    UserCreate, UserUpdate, UserOut, PlantCreate, PlantOut, DepartmentCreate, DepartmentOut,
    MachineCreate, MachineOut, DeviceCreate, DeviceOut, SystemSettingOut, AuditLogOut, NotificationOut
)
from backend.app.websocket_manager import ws_manager
from backend.app.influx_client import influx_manager

router = APIRouter()

# Stuck/frozen sensor tracking
frozen_detection_cache: Dict[int, List[float]] = {}

# Helper to log audit actions
def log_audit(db: Session, action: str, details: str, user_id: Optional[int] = None, ip_address: Optional[str] = None):
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

# Helper to add notifications
def add_notification(db: Session, user_id: int, message: str, note_type: str = "INFO"):
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

# Helper to fetch active system threshold configurations
def get_db_setting(db: Session, key: str, default: float) -> float:
    try:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            return float(setting.value)
    except Exception:
        pass
    return default

# -----------------------------------------------------
# AUTHENTICATION & SESSIONS
# -----------------------------------------------------
@router.post("/auth/login", response_model=Token)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    role = db.query(Role).filter(Role.id == user.role_id).first()
    permissions = role.permissions if role else []
    
    token_data = {"sub": user.username, "role": role.name if role else "Viewer"}
    access_token = create_access_token(data=token_data)
    
    log_audit(db, "LOGIN", f"User {user.username} logged in successfully", user.id, request.client.host)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role.name if role else "Viewer",
        "permissions": permissions
    }

@router.post("/auth/logout")
def logout(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        blacklist_token(token)
    log_audit(db, "LOGOUT", f"User {user.username} logged out", user.id, request.client.host)
    return {"status": "success", "message": "Successfully logged out"}

@router.post("/auth/forgot-password")
def forgot_password(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Prevent user enumeration, pretend successful
        return {"status": "success", "message": "Password reset token sent to your email"}
    
    reset_token = create_access_token(data={"sub": user.username, "action": "reset-password"}, expires_delta=timedelta(minutes=15))
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    print(f"[PASSWORD RESET LINK]: {reset_link}") # Print to server log for testing
    
    return {"status": "success", "message": "Password reset token sent to your email", "reset_link_mock": reset_link}

@router.get("/auth/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": role.name if role else "Viewer",
        "permissions": role.permissions if role else []
    }

# -----------------------------------------------------
# USER MANAGEMENT (Admin Protected CRUD)
# -----------------------------------------------------
@router.get("/users", response_model=List[UserOut])
def get_users(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Protect with role check
    RoleChecker(["Admin"])(user, db)
    return db.query(User).all()

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin"])(user, db)
    existing_user = db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    new_user = User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role_id=payload.role_id,
        is_active=payload.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    log_audit(db, "CREATE_USER", f"Created user {new_user.username}", user.id, request.client.host)
    return new_user

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin"])(user, db)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    if payload.email is not None:
        target.email = payload.email
    if payload.role_id is not None:
        target.role_id = payload.role_id
    if payload.is_active is not None:
        target.is_active = payload.is_active
    if payload.password is not None:
        target.password_hash = get_password_hash(payload.password)
        
    db.commit()
    db.refresh(target)
    log_audit(db, "UPDATE_USER", f"Updated user {target.username}", user.id, request.client.host)
    return target

@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin"])(user, db)
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
        
    username = target.username
    db.delete(target)
    db.commit()
    log_audit(db, "DELETE_USER", f"Deleted user {username}", user.id, request.client.host)
    return {"status": "success", "message": f"Deleted user {username}"}

# -----------------------------------------------------
# PLANT MANAGEMENT (CRUD)
# -----------------------------------------------------
@router.get("/plants", response_model=List[PlantOut])
def get_plants(db: Session = Depends(get_db)):
    return db.query(Plant).all()

@router.post("/plants", response_model=PlantOut, status_code=status.HTTP_201_CREATED)
def create_plant(payload: PlantCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    plant = Plant(
        name=payload.name,
        location=payload.location,
        timezone=payload.timezone,
        description=payload.description,
        status=payload.status
    )
    db.add(plant)
    db.commit()
    db.refresh(plant)
    log_audit(db, "CREATE_PLANT", f"Created plant {plant.name}", user.id, request.client.host)
    return plant

@router.put("/plants/{plant_id}", response_model=PlantOut)
def update_plant(plant_id: int, payload: PlantCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    
    plant.name = payload.name
    plant.location = payload.location
    plant.timezone = payload.timezone
    plant.description = payload.description
    plant.status = payload.status
    
    db.commit()
    db.refresh(plant)
    log_audit(db, "UPDATE_PLANT", f"Updated plant {plant.name}", user.id, request.client.host)
    return plant

@router.delete("/plants/{plant_id}")
def delete_plant(plant_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    
    name = plant.name
    db.delete(plant)
    db.commit()
    log_audit(db, "DELETE_PLANT", f"Deleted plant {name}", user.id, request.client.host)
    return {"status": "success", "message": f"Deleted plant {name}"}

# -----------------------------------------------------
# DEPARTMENT MANAGEMENT (CRUD)
# -----------------------------------------------------
@router.get("/departments", response_model=List[DepartmentOut])
def get_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()

@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    dept = Department(
        plant_id=payload.plant_id,
        name=payload.name,
        description=payload.description
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    log_audit(db, "CREATE_DEPARTMENT", f"Created department {dept.name}", user.id, request.client.host)
    return dept

@router.put("/departments/{dept_id}", response_model=DepartmentOut)
def update_department(dept_id: int, payload: DepartmentCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    dept.plant_id = payload.plant_id
    dept.name = payload.name
    dept.description = payload.description
    
    db.commit()
    db.refresh(dept)
    log_audit(db, "UPDATE_DEPARTMENT", f"Updated department {dept.name}", user.id, request.client.host)
    return dept

@router.delete("/departments/{dept_id}")
def delete_department(dept_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    name = dept.name
    db.delete(dept)
    db.commit()
    log_audit(db, "DELETE_DEPARTMENT", f"Deleted department {name}", user.id, request.client.host)
    return {"status": "success", "message": f"Deleted department {name}"}

# -----------------------------------------------------
# MACHINE MANAGEMENT (CRUD)
# -----------------------------------------------------
@router.get("/machines", response_model=List[MachineOut])
def get_machines(db: Session = Depends(get_db)):
    return db.query(Machine).all()

@router.post("/machines", response_model=MachineOut, status_code=status.HTTP_201_CREATED)
def create_machine(payload: MachineCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    mach = Machine(
        department_id=payload.department_id,
        name=payload.name,
        type=payload.type,
        rated_capacity=payload.rated_capacity,
        status=payload.status
    )
    db.add(mach)
    db.commit()
    db.refresh(mach)
    log_audit(db, "CREATE_MACHINE", f"Created machine {mach.name}", user.id, request.client.host)
    return mach

@router.put("/machines/{mach_id}", response_model=MachineOut)
def update_machine(mach_id: int, payload: MachineCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    mach = db.query(Machine).filter(Machine.id == mach_id).first()
    if not mach:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    mach.department_id = payload.department_id
    mach.name = payload.name
    mach.type = payload.type
    mach.rated_capacity = payload.rated_capacity
    mach.status = payload.status
    
    db.commit()
    db.refresh(mach)
    log_audit(db, "UPDATE_MACHINE", f"Updated machine {mach.name}", user.id, request.client.host)
    return mach

@router.delete("/machines/{mach_id}")
def delete_machine(mach_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    mach = db.query(Machine).filter(Machine.id == mach_id).first()
    if not mach:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    name = mach.name
    db.delete(mach)
    db.commit()
    log_audit(db, "DELETE_MACHINE", f"Deleted machine {name}", user.id, request.client.host)
    return {"status": "success", "message": f"Deleted machine {name}"}

# -----------------------------------------------------
# DEVICE MANAGEMENT (CRUD)
# -----------------------------------------------------
@router.get("/devices", response_model=List[DeviceOut])
def get_devices(db: Session = Depends(get_db)):
    return db.query(Device).all()

@router.post("/devices", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    dev = Device(
        machine_id=payload.machine_id,
        name=payload.name,
        type=payload.type,
        register_address=payload.register_address,
        unit=payload.unit,
        nominal_min=payload.nominal_min,
        nominal_max=payload.nominal_max,
        serial_number=payload.serial_number,
        firmware_version=payload.firmware_version,
        communication_status=payload.communication_status,
        is_active=payload.is_active
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)
    log_audit(db, "CREATE_DEVICE", f"Created device {dev.name}", user.id, request.client.host)
    return dev

@router.put("/devices/{dev_id}", response_model=DeviceOut)
def update_device(dev_id: int, payload: DeviceCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    dev = db.query(Device).filter(Device.id == dev_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")
    
    dev.machine_id = payload.machine_id
    dev.name = payload.name
    dev.type = payload.type
    dev.register_address = payload.register_address
    dev.unit = payload.unit
    dev.nominal_min = payload.nominal_min
    dev.nominal_max = payload.nominal_max
    dev.serial_number = payload.serial_number
    dev.firmware_version = payload.firmware_version
    dev.communication_status = payload.communication_status
    dev.is_active = payload.is_active
    
    db.commit()
    db.refresh(dev)
    log_audit(db, "UPDATE_DEVICE", f"Updated device {dev.name}", user.id, request.client.host)
    return dev

@router.delete("/devices/{dev_id}")
def delete_device(dev_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager", "Engineer"])(user, db)
    dev = db.query(Device).filter(Device.id == dev_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")
    
    name = dev.name
    db.delete(dev)
    db.commit()
    log_audit(db, "DELETE_DEVICE", f"Deleted device {name}", user.id, request.client.host)
    return {"status": "success", "message": f"Deleted device {name}"}

# -----------------------------------------------------
# BULK TELEMETRY INGESTION PIPELINE (InfluxDB Dual Write)
# -----------------------------------------------------
@router.post("/readings/bulk", status_code=status.HTTP_201_CREATED)
async def ingest_bulk_telemetry(payload: List[RawTelemetryRecord], db: Session = Depends(get_db)):
    if not payload:
        return {"status": "ok", "records_inserted": 0}

    timestamp = payload[0].timestamp
    # Idempotency check: prevent duplicate inserts if client retries same timestamp payload
    duplicate_check = db.query(SensorReading.time).filter(SensorReading.time == timestamp).first()
    if duplicate_check:
        return {"status": "ok", "records_inserted": 0, "info": "Batch already ingested"}

    broadcast_data = {
        "event": "TELEMETRY_UPDATE",
        "timestamp": timestamp.isoformat(),
        "readings": {}
    }

    # Retrieve parameters thresholds dynamically
    breaker_limit = get_db_setting(db, "alarm_threshold_breaker_max", 45000.0)
    tg_limit = get_db_setting(db, "alarm_threshold_tg_max", 30000.0)
    sms_limit = get_db_setting(db, "alarm_threshold_sms_max", 95000.0)

    influx_records = []
    for record in payload:
        # Check alarm thresholds
        check_and_trigger_alarms(record, breaker_limit, tg_limit, sms_limit, db)
        check_frozen_sensor(record, db)

        # Collect record for InfluxDB bulk write
        influx_records.append({
            "sensor_id": record.sensor_id,
            "sensor_name": record.sensor_name,
            "value": record.value,
            "quality": record.quality,
            "status": record.status,
            "plant": record.plant,
            "timestamp": record.timestamp
        })

        # Update PostgreSQL sensor_readings for operational last-state cache
        reading = SensorReading(
            time=record.timestamp,
            sensor_id=record.sensor_id,
            value=record.value,
            quality=record.quality,
            status=record.status
        )
        db.add(reading)
        
        # Build live socket broadcast payload
        broadcast_data["readings"][record.sensor_id] = {
            "name": record.sensor_name,
            "value": record.value,
            "unit": record.unit,
            "status": record.status,
            "quality": record.quality
        }

    # Write high-density telemetry in a single bulk batch
    if influx_records:
        try:
            influx_manager.write_readings(influx_records)
        except Exception as inf_err:
            print(f"[INFLUXDB WRITE ERROR]: {inf_err}")

    db.commit()

    # Dynamic KPI execution
    try:
        calculate_kpis(timestamp, db)
    except Exception as kpi_err:
        print(f"[KPI ERROR]: {kpi_err}")

    # Forecast execution
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

def check_and_trigger_alarms(record: RawTelemetryRecord, breaker_limit: float, tg_limit: float, sms_limit: float, db: Session):
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
        active_alarm = db.query(Alarm).filter(
            Alarm.sensor_id == s_id,
            Alarm.alarm_type == alarm_type,
            Alarm.status == "ACTIVE"
        ).first()
        
        if not active_alarm:
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
            # Create a notification for users
            users = db.query(User).all()
            for u in users:
                add_notification(db, u.id, f"Alarm {alarm_type} ({severity}) triggered on device {record.sensor_name}. Value: {val}", "ALARM")
    else:
        # Auto clear alarm state when returned to normal
        active_alarms = db.query(Alarm).filter(
            Alarm.sensor_id == s_id,
            Alarm.status == "ACTIVE"
        ).all()
        for alarm in active_alarms:
            # Check clearing criteria
            if ((alarm.alarm_type == "CB_OVERLOAD" and val <= breaker_limit) or
                (alarm.alarm_type == "TURBINE_OVERLOAD" and val <= tg_limit) or
                (alarm.alarm_type == "SMS_LIMIT_SURGE" and val <= sms_limit) or
                (alarm.alarm_type == "POWER_FACTOR_LOW" and val >= 0.90)):
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
                comments="Sensor value frozen static for 10 periods."
            )
            db.add(new_alarm)

def calculate_kpis(timestamp: datetime, db: Session):
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
        avg_val = np.mean(values)
        peak_val = np.max(values)
        
        load_factor = (avg_val / peak_val) if peak_val > 0 else 1.0
        
        db.add(KPIHistory(time=timestamp, equipment_id=eq_id, kpi_name="Average Load", value=avg_val, unit="kW"))
        db.add(KPIHistory(time=timestamp, equipment_id=eq_id, kpi_name="Peak Load", value=peak_val, unit="kW"))
        db.add(KPIHistory(time=timestamp, equipment_id=eq_id, kpi_name="Load Factor", value=load_factor, unit=""))
    db.commit()

def compute_moving_regression_forecast(timestamp: datetime, db: Session):
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

    running_furnaces = 0
    # SMS-4 furnaces (sensors 25, 29, 33, 37)
    for s_id in [25, 29, 33, 37]:
        if latest_readings.get(s_id, 0.0) > 50.0:
            running_furnaces += 1
            
    # SMS-1 power check
    if latest_readings.get(19, 0.0) > 100.0:
        running_furnaces += 1

    grid_power_combined = latest_readings.get(1, 0.0) + latest_readings.get(2, 0.0)
    generation_combined = latest_readings.get(41, 0.0) + latest_readings.get(42, 0.0)

    # 2. Active alarms count
    active_alarms = db.query(Alarm).filter(Alarm.status == "ACTIVE").order_by(desc(Alarm.time)).all()
    
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
        "total_machines": 5,
        "running_machines": 4 if running_furnaces > 0 else 2,
        "offline_machines": 1,
        "faulty_machines": len(active_alarms),
        "avg_pf": latest_readings.get(47, 0.929),
        "load_factor": latest_readings.get(48, 23.279),
        "today_energy_kwh": latest_readings.get(45, 93400.0),
        "monthly_energy_kwh": latest_readings.get(45, 93400.0) * 30.0,
        "carbon_emission": latest_readings.get(45, 93400.0) * 0.38, # 0.38 kg CO2 per kWh
        "energy_cost": latest_readings.get(45, 93400.0) * 0.12 # $0.12 per kWh
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
        "active_alarms_count": len(active_alarms),
        "predictions": pred_data
    }

# -----------------------------------------------------
# ADVANCED TRENDS & COMPARISONS (InfluxDB Integration)
# -----------------------------------------------------
@router.get("/trends")
def get_trends(
    sensor_id: int,
    quick_filter: Optional[str] = "1h",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    resolution: Optional[str] = "1m",
    shift: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Resolve timestamps based on quick filter or custom dates
    now = datetime.now(timezone.utc)
    if start_time is None or end_time is None:
        if quick_filter == "1h":
            start_time = now - timedelta(hours=1)
        elif quick_filter == "6h":
            start_time = now - timedelta(hours=6)
        elif quick_filter == "12h":
            start_time = now - timedelta(hours=12)
        elif quick_filter == "24h":
            start_time = now - timedelta(hours=24)
        elif quick_filter == "7d":
            start_time = now - timedelta(days=7)
            resolution = "15m"
        elif quick_filter == "30d":
            start_time = now - timedelta(days=30)
            resolution = "1h"
        elif quick_filter == "90d":
            start_time = now - timedelta(days=90)
            resolution = "1d"
        else:
            start_time = now - timedelta(hours=1)
        end_time = now

    # Convert native datetime to UTC if offset naive
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    # 1. Query InfluxDB for primary time-series data
    readings_list = []
    try:
        readings_list = influx_manager.query_readings(
            sensor_id=sensor_id,
            start_time=start_time,
            end_time=end_time,
            resolution=resolution
        )
    except Exception as inf_err:
        print(f"[INFLUXDB QUERY FALLBACK TRIGGERED]: {inf_err}")

    # 2. Fallback to SQL Database if InfluxDB returns empty
    if not readings_list:
        sql_query = db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.time >= start_time,
            SensorReading.time <= end_time
        ).order_by(SensorReading.time.asc())
        
        sql_readings = sql_query.all()
        for r in sql_readings:
            readings_list.append({
                "time": r.time,
                "sensor_id": r.sensor_id,
                "value": r.value
            })

    # Apply Shift-based filtering if requested
    # Shifts: Morning (06:00 - 14:00), Afternoon (14:00 - 22:00), Night (22:00 - 06:00)
    if shift:
        filtered_readings = []
        for r in readings_list:
            t_val = r["time"]
            # Convert timezone-aware object to local hour
            local_hour = t_val.hour
            if shift == "Morning" and (6 <= local_hour < 14):
                filtered_readings.append(r)
            elif shift == "Afternoon" and (14 <= local_hour < 22):
                filtered_readings.append(r)
            elif shift == "Night" and (local_hour >= 22 or local_hour < 6):
                filtered_readings.append(r)
        readings_list = filtered_readings

    if not readings_list:
        return {
            "sensor_id": sensor_id,
            "readings": [],
            "statistics": {
                "avg": 0.0, "min": 0.0, "max": 0.0, "median": 0.0, "std_dev": 0.0, "variance": 0.0,
                "total_consumption": 0.0, "running_hours": 0.0, "downtime_hours": 0.0, "efficiency": 0.0
            }
        }

    values = [r["value"] for r in readings_list]
    
    # Calculate statistics summary
    mean_val = float(np.mean(values))
    min_val = float(np.min(values))
    max_val = float(np.max(values))
    median_val = float(np.median(values))
    std_dev_val = float(np.std(values))
    variance_val = float(np.var(values))
    
    # Energy parameters calculations
    device = db.query(Device).filter(Device.id == sensor_id).first()
    is_power_device = device and device.unit == "kW"
    
    # Total kWh consumption (Integration of power over time interval)
    total_consumption = 0.0
    if is_power_device:
        # Assuming resolution spacing
        total_consumption = mean_val * ((end_time - start_time).total_seconds() / 3600.0)
        
    running_hours = sum(1 for v in values if v > 5.0) * ( (end_time - start_time).total_seconds() / (len(values) * 3600.0) )
    downtime_hours = ((end_time - start_time).total_seconds() / 3600.0) - running_hours
    efficiency = (running_hours / ((end_time - start_time).total_seconds() / 3600.0)) * 100.0 if running_hours > 0 else 0.0

    return {
        "sensor_id": sensor_id,
        "readings": [{"time": r["time"].isoformat(), "value": r["value"]} for r in readings_list],
        "statistics": {
            "avg": round(mean_val, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "median": round(median_val, 2),
            "std_dev": round(std_dev_val, 2),
            "variance": round(variance_val, 2),
            "total_consumption": round(total_consumption, 2),
            "running_hours": round(running_hours, 2),
            "downtime_hours": round(downtime_hours, 2),
            "efficiency": round(efficiency, 1)
        }
    }

# -----------------------------------------------------
# ADVANCED ANALYTICS (Analytics Page widgets)
# -----------------------------------------------------
@router.get("/analytics")
def get_advanced_analytics(db: Session = Depends(get_db)):
    # 1. Highest Energy Machine
    # SMS-1 (sensor 19) and SMS-4 (sensor 22) are main consumers
    sms1_last = db.query(SensorReading).filter(SensorReading.sensor_id == 19).order_by(desc(SensorReading.time)).first()
    sms4_last = db.query(SensorReading).filter(SensorReading.sensor_id == 22).order_by(desc(SensorReading.time)).first()
    
    sms1_val = sms1_last.value if sms1_last else 51135.0
    sms4_val = sms4_last.value if sms4_last else 26163.0
    
    highest_machine = "SMS-1 Electric Arc Furnace" if sms1_val > sms4_val else "SMS-4 Refining Furnace"
    highest_value = max(sms1_val, sms4_val)

    # 2. Lowest Power Factor
    pf_reading = db.query(SensorReading).filter(SensorReading.sensor_id == 47).order_by(desc(SensorReading.time)).first()
    lowest_pf = pf_reading.value if pf_reading else 0.929

    # 3. Peak Demand
    cb1_reading = db.query(SensorReading).filter(SensorReading.sensor_id == 1).order_by(desc(SensorReading.time)).first()
    cb2_reading = db.query(SensorReading).filter(SensorReading.sensor_id == 2).order_by(desc(SensorReading.time)).first()
    peak_demand = (cb1_reading.value if cb1_reading else 22860.0) + (cb2_reading.value if cb2_reading else 19888.0)

    # 4. Hourly Consumption Mock layout
    now = datetime.now()
    hourly_consumption = []
    for h in range(24):
        hour_time = now - timedelta(hours=24-h)
        hourly_consumption.append({
            "hour": hour_time.strftime("%H:00"),
            "value": round(7500.0 + np.sin(h/3.0)*1500.0 + np.random.normal(0, 300), 2)
        })

    # 5. Shift-wise Consumption
    shift_consumption = [
        {"shift": "Morning (06:00-14:00)", "value": 68400.0},
        {"shift": "Afternoon (14:00-22:00)", "value": 72100.0},
        {"shift": "Night (22:00-06:00)", "value": 58900.0}
    ]

    # 6. Load Distribution
    load_distribution = [
        {"name": "SMS-1 Furnace", "value": round((sms1_val / peak_demand)*100, 1) if peak_demand > 0 else 55.0},
        {"name": "SMS-4 Furnace", "value": round((sms4_val / peak_demand)*100, 1) if peak_demand > 0 else 30.0},
        {"name": "Auxiliaries & Lighting", "value": 15.0}
    ]

    # 7. Carbon footprint & Energy costs
    total_today_kwh = (cb1_reading.value + cb2_reading.value) if (cb1_reading and cb2_reading) else 42748.0
    energy_cost = total_today_kwh * 0.12  # $0.12/kWh
    carbon_footprint = total_today_kwh * 0.38  # 0.38 kg CO2/kWh

    return {
        "highest_energy_machine": {
            "name": highest_machine,
            "current_load_kw": round(highest_value, 2)
        },
        "lowest_power_factor": round(lowest_pf, 3),
        "peak_demand_kw": round(peak_demand, 2),
        "hourly_consumption": hourly_consumption,
        "shift_wise_consumption": shift_consumption,
        "load_distribution": load_distribution,
        "machine_utilization": [
            {"machine": "SMS-1", "utilization": 82.5},
            {"machine": "SMS-2", "utilization": 0.0},
            {"machine": "SMS-4", "utilization": 87.2},
            {"machine": "TG-2 Turbine", "utilization": 95.0}
        ],
        "energy_cost_usd": round(energy_cost, 2),
        "carbon_footprint_kg_co2": round(carbon_footprint, 2),
        "efficiency_score": 88.4
    }

# -----------------------------------------------------
# ALARMS CONSOLE API
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
def acknowledge_alarm(alarm_id: int, payload: AlarmAcknowledge, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alarm = db.query(Alarm).filter(Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found.")
        
    alarm.status = "ACKNOWLEDGED"
    alarm.acknowledged_by = payload.acknowledged_by
    alarm.comments = payload.comments
    db.commit()
    
    log_audit(db, "ACKNOWLEDGE_ALARM", f"User acknowledged alarm #{alarm_id}: {payload.comments}", user.id, request.client.host)
    return {"status": "success", "alarm_id": alarm_id, "state": "ACKNOWLEDGED"}

# -----------------------------------------------------
# REPORTS GENERATION API
# -----------------------------------------------------
@router.get("/reports", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_db)):
    return db.query(Report).order_by(desc(Report.created_at)).all()

@router.post("/reports/generate")
def generate_report(payload: dict, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report_type = payload.get("report_type", "DAILY")
    file_format = payload.get("format", "CSV")
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"ieip_analytics_{report_type.lower()}_{timestamp_str}.csv"
    
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, report_name)
    
    # Fetch historical readings for report compilation
    readings = db.query(SensorReading).order_by(desc(SensorReading.time)).limit(200).all()
    
    with open(file_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["=== INDUSTRIAL ENERGY INTELLIGENCE PLATFORM (IEIP) ==="])
        writer.writerow([f"Report Type: {report_type}", f"Generated By: {user.username}", f"Date: {datetime.now().isoformat()}"])
        writer.writerow([])
        writer.writerow(["Timestamp", "Device ID", "Value", "Quality", "Status"])
        for r in readings:
            writer.writerow([r.time.isoformat(), r.sensor_id, r.value, r.quality, r.status])
            
    new_report = Report(
        name=report_name,
        report_type=report_type,
        format=file_format,
        file_path=file_path
    )
    db.add(new_report)
    db.commit()
    
    log_audit(db, "GENERATE_REPORT", f"Generated {report_type} report saved to {report_name}", user.id, request.client.host)
    return {"status": "success", "report_id": new_report.id, "file_name": report_name}

# -----------------------------------------------------
# SETTINGS & LIMITS CONFIGURATION
# -----------------------------------------------------
@router.get("/settings", response_model=List[SystemSettingOut])
def get_system_settings(db: Session = Depends(get_db)):
    return db.query(SystemSetting).all()

@router.post("/settings")
def update_system_settings(payload: dict, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    
    updated = []
    for k, v in payload.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == k).first()
        if setting:
            setting.value = str(v)
            updated.append(k)
        else:
            new_setting = SystemSetting(key=k, value=str(v))
            db.add(new_setting)
            updated.append(k)
            
    db.commit()
    log_audit(db, "UPDATE_SETTINGS", f"Updated limit configurations: {', '.join(updated)}", user.id, request.client.host)
    return {"status": "success", "updated_settings": updated}

# -----------------------------------------------------
# AUDIT LOGS & NOTIFICATIONS
# -----------------------------------------------------
@router.get("/audit-logs", response_model=List[AuditLogOut])
def get_audit_logs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Plant Manager"])(user, db)
    return db.query(AuditLog).order_by(desc(AuditLog.time)).limit(100).all()

@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id == user.id).order_by(desc(Notification.created_at)).all()

@router.put("/notifications/{note_id}/read")
def mark_notification_read(note_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(Notification).filter(Notification.id == note_id, Notification.user_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Notification not found")
    note.read = True
    db.commit()
    return {"status": "success"}

# -----------------------------------------------------
# AI-READY PLATFORMS (Future integrations placeholders)
# -----------------------------------------------------
@router.post("/analytics/anomaly-detection")
def run_ai_anomaly_detection(user: User = Depends(get_current_user)):
    return {
        "status": "success",
        "model": "Autoencoder PyTorch Neural Net v1.0",
        "anomalies_detected_last_24h": 2,
        "details": "No novel operational anomalies detected in raw current sequences.",
        "future_integration": "Connected to Celery Background ML Worker"
    }

@router.post("/analytics/predictive-maintenance")
def run_ai_predictive_maintenance(user: User = Depends(get_current_user)):
    return {
        "status": "success",
        "target": "Electric Arc Furnace Electrode degradation index",
        "estimated_remaining_useful_life_hours": 142.6,
        "recommended_replacement_date": (datetime.now() + timedelta(days=6)).date().isoformat()
    }

@router.post("/analytics/demand-forecasting")
def run_ai_demand_forecasting(user: User = Depends(get_current_user)):
    return {
        "status": "success",
        "model": "PatchTST Transformer",
        "forecast_horizon_hours": 24,
        "peak_expected_time": "14:30:00",
        "peak_expected_load_kw": 88400.0
    }
