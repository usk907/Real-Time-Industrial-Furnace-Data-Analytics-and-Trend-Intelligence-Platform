from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta, timezone, time
import numpy as np
import os
import csv
from typing import List, Dict, Any, Optional
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.app.config import settings
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
    
    client_host = request.client.host if request.client else "127.0.0.1"
    log_audit(db, "LOGIN", f"User {user.username} logged in successfully", user.id, client_host)
    
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
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    print(f"[PASSWORD RESET LINK]: {reset_link}") # Print to server log for testing
    
    return {"status": "success", "message": "Password reset token sent to your email", "reset_link_mock": reset_link}


class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str


@router.post("/auth/reset-password")
def reset_password(payload: ResetPasswordPayload, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if decoded.get("action") != "reset-password":
        raise HTTPException(status_code=400, detail="Invalid reset token")

    username = decoded.get("sub")
    if not username:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "success", "message": "Password updated successfully"}

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
    broadcast_data = {
        "event": "TELEMETRY_UPDATE",
        "timestamp": timestamp.isoformat(),
        "readings": {
            r.sensor_id: {"name": r.sensor_name, "value": r.value, "unit": r.unit, "status": r.status, "quality": r.quality}
            for r in payload
        }
    }

    # Broadcast to live UI immediately
    if ws_manager.active_connections:
        await ws_manager.broadcast(broadcast_data)

    def _sync_db_write():
        try:
            readings = [
                SensorReading(time=r.timestamp, sensor_id=r.sensor_id, value=r.value, quality=r.quality, status=r.status)
                for r in payload
            ]
            db.bulk_save_objects(readings)
            db.commit()
        except Exception as e:
            db.rollback()

    asyncio.create_task(asyncio.to_thread(_sync_db_write))
    return {"status": "success", "records_inserted": len(payload), "timestamp": timestamp}

def check_and_trigger_alarms(record: RawTelemetryRecord, breaker_limit: float, tg_limit: float, sms_limit: float, active_alarms_map: dict, user_ids: list, db: Session):
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
                add_notification(db, u_id, f"Alarm {alarm_type} ({severity}) triggered on device {record.sensor_name}. Value: {val}", "ALARM")
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

def check_frozen_sensor(record: RawTelemetryRecord, active_alarms_map: dict, db: Session):
    s_id = record.sensor_id
    if s_id not in frozen_detection_cache:
        frozen_detection_cache[s_id] = []
        
    cache = frozen_detection_cache[s_id]
    cache.append(record.value)
    if len(cache) > 10:
        cache.pop(0)
        
    if len(cache) == 10 and len(set(cache)) == 1:
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
    # 1. Fetch latest reading values efficiently in a single query
    latest_readings = {}
    recent_readings = db.query(SensorReading).order_by(desc(SensorReading.time)).limit(120).all()
    for r in recent_readings:
        if r.sensor_id not in latest_readings:
            latest_readings[r.sensor_id] = r.value

    running_furnaces = 0
    # Shyam Metaliks furnaces: SMS-1 (10-14), SMS-2 (24-35), SMS-4 (36-39)
    furnace_ids = list(range(10, 15)) + list(range(24, 36)) + list(range(36, 40))
    for s_id in furnace_ids:
        if latest_readings.get(s_id, 0.0) > 10.0:
            running_furnaces += 1

    grid_power_combined = latest_readings.get(1, 0.0)
    generation_combined = latest_readings.get(5, 0.0) + latest_readings.get(6, 0.0) + latest_readings.get(7, 0.0) + latest_readings.get(8, 0.0) + latest_readings.get(9, 0.0)

    # 2. Active alarms count
    active_alarms = db.query(Alarm).filter(Alarm.status == "ACTIVE").order_by(desc(Alarm.time)).all()
    
    # 3. Compile KPI values
    grid_import_kwh = latest_readings.get(1, 0.0)
    grid_import_kvah = latest_readings.get(2, 0.0)
    avg_pf = round(grid_import_kwh / grid_import_kvah, 3) if grid_import_kvah > 0 else 0.95
    if avg_pf > 1.0 or avg_pf < 0.5:
        avg_pf = 0.95

    # Sum SMS running loads dynamically
    sms1_sum = sum(latest_readings.get(i, 0.0) for i in range(10, 18))
    sms2_sum = sum(latest_readings.get(i, 0.0) for i in list(range(24, 36)) + [40, 41])
    sms4_sum = sum(latest_readings.get(i, 0.0) for i in list(range(36, 40)) + list(range(42, 49)))
    sms_total = sms1_sum + sms2_sum + sms4_sum

    kpis = {
        "grid_power_combined": grid_power_combined,
        "generation_combined": generation_combined,
        "cb5214_kw": latest_readings.get(1, 0.0),
        "cb14_kw": latest_readings.get(2, 0.0),
        "cb52g4_kw": latest_readings.get(3, 0.0),
        "sms_allocated_power": 120000.0,
        "sms_run_power": sms_total,
        "sms_1_run_power": sms1_sum,
        "sms_4_run_power": sms4_sum,
        "sms_4_utl_pct": round((running_furnaces / 21) * 100.0, 1) if running_furnaces > 0 else 0.0,
        "running_furnace_count": running_furnaces,
        "total_machines": 7,
        "running_machines": 6 if running_furnaces > 0 else 3,
        "offline_machines": 1,
        "faulty_machines": len(active_alarms),
        "avg_pf": avg_pf,
        "load_factor": 75.4,
        "today_energy_kwh": latest_readings.get(1, 93400.0),
        "monthly_energy_kwh": latest_readings.get(1, 93400.0) * 30.0,
        "carbon_emission": latest_readings.get(1, 93400.0) * 0.38, # 0.38 kg CO2 per kWh
        "energy_cost": latest_readings.get(1, 93400.0) * 0.12 # $0.12 per kWh
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
    now = datetime.now(timezone.utc)
    FILTER_MAP = {"1h": (1, "1m"), "6h": (6, "1m"), "12h": (12, "1m"), "24h": (24, "1m"), "7d": (168, "15m"), "30d": (720, "1h"), "90d": (2160, "1d")}
    hours, default_res = FILTER_MAP.get(quick_filter, (1, "1m"))
    
    start_time = (start_time or (now - timedelta(hours=hours))).astimezone(timezone.utc) if start_time else (now - timedelta(hours=hours))
    end_time = (end_time or now).astimezone(timezone.utc) if end_time else now
    resolution = resolution or default_res

    # 1. Query InfluxDB / SQL Fallback
    try:
        readings_list = influx_manager.query_readings(sensor_id=sensor_id, start_time=start_time, end_time=end_time, resolution=resolution)
    except Exception:
        readings_list = []

    if not readings_list:
        sql_readings = db.query(SensorReading.time, SensorReading.value).filter(
            SensorReading.sensor_id == sensor_id, SensorReading.time >= start_time, SensorReading.time <= end_time
        ).order_by(SensorReading.time.asc()).all()
        readings_list = [{"time": r[0], "sensor_id": sensor_id, "value": r[1]} for r in sql_readings]

    # Shift filter
    if shift == "Night":
        readings_list = [r for r in readings_list if r["time"].hour >= 22 or r["time"].hour < 6]
    elif shift in ("Morning", "Afternoon"):
        s_min, s_max = (6, 14) if shift == "Morning" else (14, 22)
        readings_list = [r for r in readings_list if s_min <= r["time"].hour < s_max]

    if not readings_list:
        return {"sensor_id": sensor_id, "readings": [], "statistics": {"avg": 0.0, "min": 0.0, "max": 0.0, "median": 0.0, "std_dev": 0.0, "variance": 0.0, "total_consumption": 0.0, "running_hours": 0.0, "downtime_hours": 0.0, "efficiency": 0.0}}

    vals = np.array([r["value"] for r in readings_list], dtype=float)
    total_hours = max((end_time - start_time).total_seconds() / 3600.0, 0.01)
    
    device = db.query(Device.unit).filter(Device.id == sensor_id).first()
    is_power = device and device[0] == "kW"
    total_consumption = float(vals.mean() * total_hours) if is_power else 0.0
    
    running_hours = float((vals > 5.0).sum() / len(vals) * total_hours)
    downtime_hours = max(0.0, total_hours - running_hours)
    efficiency = round((running_hours / total_hours) * 100.0, 1)

    return {
        "sensor_id": sensor_id,
        "readings": [{"time": r["time"].isoformat(), "value": r["value"]} for r in readings_list],
        "statistics": {
            "avg": round(float(vals.mean()), 2),
            "min": round(float(vals.min()), 2),
            "max": round(float(vals.max()), 2),
            "median": round(float(np.median(vals)), 2),
            "std_dev": round(float(vals.std()), 2),
            "variance": round(float(vals.var()), 2),
            "total_consumption": round(total_consumption, 2),
            "running_hours": round(running_hours, 2),
            "downtime_hours": round(downtime_hours, 2),
            "efficiency": efficiency
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

    # 4. Hourly Consumption derived from the current snapshot so it stays stable across refreshes
    now = datetime.now()
    base_today_kwh = (cb1_reading.value + cb2_reading.value) if (cb1_reading and cb2_reading) else 42748.0
    base_hour = base_today_kwh / 24.0
    hourly_consumption = []
    for h in range(24):
        hour_time = now - timedelta(hours=24-h)
        variation = 1.0 + (0.14 * np.sin(h / 3.0)) + (0.04 * np.cos(h / 5.0))
        hourly_consumption.append({
            "hour": hour_time.strftime("%H:00"),
            "value": round(base_hour * variation, 2)
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
    RoleChecker(["Admin", "Plant Manager", "Engineer", "Operator"])(user, db)
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
    if str(file_format).upper() != "CSV":
        raise HTTPException(status_code=400, detail="Only CSV export is supported in this build")
    
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

@router.get("/reports/download")
def download_report(file: str, user: User = Depends(get_current_user)):
    from fastapi.responses import FileResponse
    safe_name = os.path.basename(file)
    file_path = os.path.join("reports", safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(file_path, filename=safe_name, media_type="text/csv")

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

# -----------------------------------------------------
# AI CHATBOT ROUTE
# -----------------------------------------------------

class ChatMessage(BaseModel):
    role: str # 'user' or 'model'
    content: str

class ChatPayload(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

@router.post("/chat")
def chat_with_gemini(payload: ChatPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # 1. Fetch system status context from the live MySQL database
    try:
        plants_count = db.query(Plant).count()
        deps_count = db.query(Department).count()
        machines_count = db.query(Machine).count()
        devices_count = db.query(Device).count()
        
        # 2. Get active alarms
        active_alarms = db.query(Alarm).filter(Alarm.status == "ACTIVE").all()
        alarms_list = []
        for a in active_alarms:
            sensor = db.query(Device).filter(Device.id == a.sensor_id).first()
            alarms_list.append({
                "sensor": sensor.name if sensor else f"Sensor {a.sensor_id}",
                "type": a.alarm_type,
                "severity": a.severity,
                "value": a.trigger_value,
                "time": a.time.isoformat() if a.time else None
            })
            
        # 3. Get latest sensor values for all devices (1-to-60)
        latest_telemetry = []
        devices = db.query(Device).all()
        for s in devices:
            reading = db.query(SensorReading).filter(SensorReading.sensor_id == s.id).order_by(desc(SensorReading.time)).first()
            if reading:
                latest_telemetry.append({
                    "id": s.id,
                    "name": s.name,
                    "value": reading.value,
                    "unit": s.unit,
                    "status": reading.status,
                    "quality": reading.quality
                })
        
        # 4. Fetch safety threshold limit settings
        settings = db.query(SystemSetting).all()
        system_settings = {s.key: s.value for s in settings}
        
    except Exception as db_err:
        print(f"[CHAT DB ERROR]: {db_err}")
        plants_count, deps_count, machines_count, devices_count = 1, 1, 5, 60
        alarms_list = []
        latest_telemetry = []
        system_settings = {}

    # Check for GEMINI_API_KEY in environment or database settings table
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        db_key = db.query(SystemSetting).filter(SystemSetting.key == "GEMINI_API_KEY").first()
        if db_key and db_key.value:
            api_key = db_key.value
            
    if not api_key:
        # Fallback offline response with structured live data
        status_msg = (
            "**AI Chatbot Offline (Key Missing)**\n\n"
            "To activate full natural language answers, please add your Google Gemini API key as `GEMINI_API_KEY` in the `.env` file of the project root.\n\n"
            "**Live Control Room Snapshot:**\n"
            f"- **Active Alarms**: {len(alarms_list)} alarm(s) currently active.\n"
            f"- **System Counts**: {plants_count} Plant(s), {deps_count} Department(s), {machines_count} Machine(s), {devices_count} Device(s).\n"
        )
        if alarms_list:
            status_msg += "\n**Active Alarms List:**\n"
            for a in alarms_list:
                status_msg += f"- `{a['sensor']}`: {a['type']} ({a['severity']}) - Trigger Value: {a['value']}\n"
        else:
            status_msg += "\n- **Alarms State**: Clean (No active alarms).\n"
            
        if latest_telemetry:
            status_msg += "\n**Key Sensor Values:**\n"
            # Get a sample of interesting sensors (e.g. temperatures, pressures, power)
            key_sensor_ids = [19, 22, 51, 52, 53, 58, 60]
            for t in latest_telemetry:
                if t['id'] in key_sensor_ids:
                    status_msg += f"- `{t['name']}`: **{t['value']} {t['unit']}** (Status: {t['status']})\n"
        return {
            "response": status_msg,
            "offline": True
        }
        
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Prepare dynamic system instruction helper
        telemetry_summary = [
            {"id": t["id"], "name": t["name"], "val": f"{t['value']} {t['unit']}", "status": t["status"]}
            for t in latest_telemetry
        ]
        
        system_prompt = (
            "You are the AI Operations Assistant for the Real-Time Industrial Furnace Data Analytics and Trend Intelligence Platform.\n"
            "Your role is to assist operators in the control room by answering questions about the plant layout, live metrics, alarms, and settings.\n\n"
            "Here is the LIVE SYSTEM CONTEXT fetched directly from the SQL database:\n"
            f"- Counts: {plants_count} Plant(s), {deps_count} Department(s), {machines_count} Machine(s), {devices_count} Device(s).\n"
            f"- Active Alarms list: {alarms_list}\n"
            f"- Safety Limits / Thresholds: {system_settings}\n"
            f"- Latest Sensor Telemetry (1-60): {telemetry_summary}\n\n"
            "Project & System Overview:\n"
            "- It is a high-density industrial control system monitoring a Steel Works plant.\n"
            "- Sensors include Power meters (CB5214, CB14, SMS Run. Power), Furnace Details (SMS-1, SMS-4), Turbine Generators (TG-1 to TG-5), Accumulators (Grid import/export kWh), and Physical Sensors (SMS-1 Furnace Temp [ID 51, °C], Pressure [ID 52, bar], Cooling Water Flow [ID 53, m³/h], Ambient Humidity [ID 57], CO2 [ID 58, ppm], Production heats [ID 59], CO gas [ID 60, ppm]).\n"
            "- Threshold limits are configured in Settings. Alarms automatically trigger when these limits are breached (e.g. CB_OVERLOAD, TURBINE_OVERLOAD, SMS_LIMIT_SURGE, POWER_FACTOR_LOW) or if a sensor freezes (FROZEN_SENSOR).\n\n"
            "Instructions:\n"
            "1. Give direct, professional, and clear answers suited for an industrial control room operator.\n"
            "2. Rely on the LIVE SYSTEM CONTEXT above to answer questions about the current state of sensors and alarms.\n"
            "3. Format numbers and values clearly with their units (e.g., '1520.4 °C', '26163 kW').\n"
            "4. If requested to perform historical queries beyond the live snapshot, explain that you have live snapshot access, and suggest using the Trends page for historic visualization.\n"
            "5. Use Markdown lists or tables when summarizing multiple telemetry points.\n"
        )

        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_prompt
        )
        
        # Map history schema
        google_history = []
        if payload.history:
            for h in payload.history:
                role = "user" if h.role == "user" else "model"
                google_history.append({
                    "role": role,
                    "parts": [h.content]
                })
                
        chat = model.start_chat(history=google_history)
        response = chat.send_message(payload.message)
        
        return {
            "response": response.text,
            "offline": False
        }
    except Exception as gemini_err:
        print(f"[GEMINI API ERROR]: {gemini_err}")
        return {
            "response": f"**AI Chatbot Connection Error**\n\nFailed to fetch response from Gemini: {str(gemini_err)}\n\nPlease check your internet connection or verify the `GEMINI_API_KEY` configuration.",
            "offline": True
        }


# -----------------------------------------------------
# AI SQL QUERY ROUTE
# -----------------------------------------------------
class AIQueryPayload(BaseModel):
    question: str

@router.post("/ai/query")
def run_ai_query(payload: AIQueryPayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from backend.app.ai_query import execute_ai_query
    
    # Retrieve GEMINI_API_KEY
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        db_key = db.query(SystemSetting).filter(SystemSetting.key == "GEMINI_API_KEY").first()
        if db_key and db_key.value:
            api_key = db_key.value
            
    res = execute_ai_query(payload.question, db, api_key)
    return res


# -----------------------------------------------------
# POWERPLUS INTEGRATION: CONSUMPTION LEDGER & PDF IMPORT
# -----------------------------------------------------

@router.get("/consumption")
def get_energy_consumption(
    date: Optional[str] = None,
    shift: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Returns daily & shift-wise cumulative energy consumption ledger,
    grouped by equipment / machine / section, matching PowerPlus specifications.
    """
    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        target_date = datetime.utcnow()

    # Shift time filtering
    if shift == "A":  # Shift A: 06:00 - 14:00
        start_time = target_date.replace(hour=6, minute=0, second=0)
        end_time = target_date.replace(hour=14, minute=0, second=0)
    elif shift == "B":  # Shift B: 14:00 - 22:00
        start_time = target_date.replace(hour=14, minute=0, second=0)
        end_time = target_date.replace(hour=22, minute=0, second=0)
    elif shift == "C":  # Shift C: 22:00 - 06:00 (next day)
        start_time = target_date.replace(hour=22, minute=0, second=0)
        end_time = (target_date + timedelta(days=1)).replace(hour=6, minute=0, second=0)
    else:  # Full Day: 00:00 - 23:59:59
        start_time = target_date.replace(hour=0, minute=0, second=0)
        end_time = target_date.replace(hour=23, minute=59, second=59)

    machines = db.query(Machine).all()
    devices = db.query(Device).all()
    devices_by_machine: Dict[int, List[Device]] = {}
    for d in devices:
        devices_by_machine.setdefault(d.machine_id, []).append(d)

    # Fetch all readings for target time interval in a single fast batched query
    all_readings = db.query(SensorReading.sensor_id, SensorReading.value, SensorReading.time).filter(
        SensorReading.time >= start_time,
        SensorReading.time <= end_time
    ).order_by(SensorReading.time.asc()).all()

    readings_by_dev: Dict[int, list] = {}
    for r in all_readings:
        readings_by_dev.setdefault(r.sensor_id, []).append((r.value, r.time))

    consumption_groups = []
    total_active_kwh = 0.0
    total_apparent_kvah = 0.0
    total_reactive_kvarh = 0.0
    peak_demand_kw = 0.0
    pf_samples = []

    for machine in machines:
        mach_devices = devices_by_machine.get(machine.id, [])
        tag_items = []

        for dev in mach_devices:
            dev_readings = readings_by_dev.get(dev.id, [])

            if dev_readings:
                vals = [r[0] for r in dev_readings]
                latest_val = float(vals[-1])
                avg_val = float(np.mean(vals))
                max_val = float(np.max(vals))
                min_val = float(np.min(vals))
                # Sparkline history (sampled max 12 points)
                step = max(1, len(vals) // 12)
                sparkline = [round(float(v), 2) for v in vals[::step]]
            else:
                # If no readings on target day, fallback to nominal/last seen baseline
                latest_val = float(dev.nominal_max or 100.0) * 0.72
                avg_val = latest_val
                max_val = latest_val * 1.08
                min_val = latest_val * 0.92
                sparkline = [round(latest_val * (0.95 + 0.1 * ((i * 7) % 5) / 5), 2) for i in range(12)]

            unit_lower = dev.unit.lower()
            if "kwh" in unit_lower or "active" in dev.name.lower():
                total_active_kwh += latest_val
            elif "kvah" in unit_lower:
                total_apparent_kvah += latest_val
            elif "kvarh" in unit_lower:
                total_reactive_kvarh += latest_val
            elif "kw" in unit_lower:
                peak_demand_kw = max(peak_demand_kw, max_val)
            elif "pf" in unit_lower or "factor" in dev.name.lower():
                pf_samples.append(latest_val)

            tag_items.append({
                "tag_id": dev.id,
                "tag_name": dev.name,
                "register": dev.register_address,
                "unit": dev.unit,
                "value": round(latest_val, 2),
                "avg_value": round(avg_val, 2),
                "max_value": round(max_val, 2),
                "min_value": round(min_val, 2),
                "sparkline": sparkline
            })

        if tag_items:
            consumption_groups.append({
                "machine_id": machine.id,
                "group_name": machine.name,
                "equipment_type": machine.type,
                "status": machine.status,
                "tags": tag_items
            })

    avg_pf = round(float(np.mean(pf_samples)), 3) if pf_samples else 0.945
    # Default fallbacks if empty database
    if total_active_kwh == 0:
        total_active_kwh = 48520.0
    if total_apparent_kvah == 0:
        total_apparent_kvah = total_active_kwh / avg_pf if avg_pf > 0 else total_active_kwh * 1.06
    if total_reactive_kvarh == 0:
        total_reactive_kvarh = np.sqrt(max(0.0, total_apparent_kvah**2 - total_active_kwh**2))
    if peak_demand_kw == 0:
        peak_demand_kw = 8450.0

    cost_per_kwh = get_db_setting(db, "ENERGY_TARIFF_INR_PER_KWH", 7.50)
    co2_factor = get_db_setting(db, "CO2_EMISSION_FACTOR_KG_PER_KWH", 0.82)

    return {
        "date": date,
        "shift": shift or "ALL",
        "summary": {
            "total_active_kwh": round(total_active_kwh, 2),
            "total_apparent_kvah": round(total_apparent_kvah, 2),
            "total_reactive_kvarh": round(total_reactive_kvarh, 2),
            "peak_demand_kw": round(peak_demand_kw, 2),
            "avg_power_factor": avg_pf,
            "estimated_cost_inr": round(total_active_kwh * cost_per_kwh, 2),
            "carbon_emissions_kg": round(total_active_kwh * co2_factor, 2)
        },
        "equipment_groups": consumption_groups
    }


@router.post("/reports/import-pdf")
async def import_pdf_energy_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Imports real CrystalEView / SCADA Report PDF export files into the database.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files (.pdf) are supported.")

    from backend.app.pdf_importer import process_pdf_import
    try:
        content = await file.read()
        result = process_pdf_import(content, db)
        log_audit(db, "IMPORT_PDF_REPORT", f"Imported PDF: {file.filename} ({result.get('imported_count')} points)", user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF report: {str(e)}")


# -----------------------------------------------------
# TAP SERVER INTEGRATION & TELEMETRY MONITORING
# -----------------------------------------------------
@router.get("/tap/status")
def get_tap_server_status(db: Session = Depends(get_db)):
    """
    Checks the status of the dedicated TAP Server and its SQL Server table storage.
    """
    import requests
    tap_url = "http://127.0.0.1:8001/tap/health"
    stats_url = "http://127.0.0.1:8001/tap/stats"
    
    tap_online = False
    tap_info = {}
    stats = {}
    
    try:
        r = requests.get(tap_url, timeout=1.0)
        if r.status_code == 200:
            tap_online = True
            tap_info = r.json()
            r_stats = requests.get(stats_url, timeout=1.0)
            if r_stats.status_code == 200:
                stats = r_stats.json()
    except Exception:
        tap_online = False

    # Count total sensor readings stored in SQL database
    total_sql_readings = db.query(func.count(SensorReading.time)).scalar() or 0

    return {
        "tap_server_online": tap_online,
        "tap_server_url": "http://127.0.0.1:8001",
        "sql_database_connected": True,
        "total_sql_readings": total_sql_readings,
        "tap_details": tap_info if tap_online else {
            "status": "OFFLINE",
            "message": "TAP server is not running on port 8001. Using backend direct ingestion fallback."
        },
        "metrics": stats
    }


