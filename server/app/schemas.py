from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from typing import List, Optional

# -----------------------------------------------------
# Auth & User Schemas
# -----------------------------------------------------
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    permissions: List[str]

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role_id: int
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# -----------------------------------------------------
# Plant Management Schemas
# -----------------------------------------------------
class PlantBase(BaseModel):
    name: str
    location: Optional[str] = None
    timezone: Optional[str] = "UTC"
    description: Optional[str] = None
    status: Optional[str] = "ACTIVE"

class PlantCreate(PlantBase):
    pass

class PlantOut(PlantBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# -----------------------------------------------------
# Department Management Schemas
# -----------------------------------------------------
class DepartmentBase(BaseModel):
    plant_id: int
    name: str
    description: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentOut(DepartmentBase):
    id: int
    class Config:
        from_attributes = True

# -----------------------------------------------------
# Machine Management Schemas
# -----------------------------------------------------
class MachineBase(BaseModel):
    department_id: int
    name: str
    type: str
    rated_capacity: Optional[float] = 0.0
    status: Optional[str] = "STOPPED"

class MachineCreate(MachineBase):
    pass

class MachineOut(MachineBase):
    id: int
    class Config:
        from_attributes = True

# -----------------------------------------------------
# Device Management Schemas
# -----------------------------------------------------
class DeviceBase(BaseModel):
    machine_id: int
    name: str
    type: str
    register_address: str
    unit: str
    nominal_min: Optional[float] = None
    nominal_max: Optional[float] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    communication_status: Optional[str] = "ONLINE"
    is_active: Optional[bool] = True

class DeviceCreate(DeviceBase):
    pass

class DeviceOut(DeviceBase):
    id: int
    last_seen: datetime
    installation_date: datetime
    class Config:
        from_attributes = True

# -----------------------------------------------------
# Telemetry Schemas
# -----------------------------------------------------
class RawTelemetryRecord(BaseModel):
    timestamp: datetime
    sensor_id: int
    sensor_name: str
    plant: str
    unit: str
    value: float
    quality: str = "GOOD"
    status: str = "OK"

class ReadingOut(BaseModel):
    time: datetime
    sensor_id: int
    value: float
    quality: str
    status: str
    class Config:
        from_attributes = True

# -----------------------------------------------------
# Alarm Schemas
# -----------------------------------------------------
class AlarmOut(BaseModel):
    id: int
    time: datetime
    end_time: Optional[datetime] = None
    sensor_id: int
    alarm_type: str
    severity: str
    trigger_value: Optional[float] = None
    status: str
    acknowledged_by: Optional[str] = None
    comments: Optional[str] = None
    class Config:
        from_attributes = True

class AlarmAcknowledge(BaseModel):
    acknowledged_by: str
    comments: str

# -----------------------------------------------------
# Report Schemas
# -----------------------------------------------------
class ReportOut(BaseModel):
    id: int
    created_at: datetime
    name: str
    report_type: str
    format: str
    file_path: str
    class Config:
        from_attributes = True

# -----------------------------------------------------
# Setting & Log Schemas
# -----------------------------------------------------
class SystemSettingOut(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    updated_at: datetime
    class Config:
        from_attributes = True

class AuditLogOut(BaseModel):
    id: int
    time: datetime
    user_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    class Config:
        from_attributes = True

class NotificationOut(BaseModel):
    id: int
    user_id: int
    message: str
    type: str
    read: bool
    created_at: datetime
    class Config:
        from_attributes = True
