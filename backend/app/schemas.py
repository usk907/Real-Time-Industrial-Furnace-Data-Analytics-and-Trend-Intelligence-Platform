from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import List, Optional

# -----------------------------------------------------
# User & Auth Schemas
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

class UserOut(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# -----------------------------------------------------
# Sensor & Telemetry Schemas
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

class SensorOut(BaseModel):
    id: int
    equipment_id: int
    name: str
    type: str
    register_address: str
    unit: str
    nominal_min: Optional[float] = None
    nominal_max: Optional[float] = None
    is_active: bool
    class Config:
        from_attributes = True

class EquipmentOut(BaseModel):
    id: int
    area_id: int
    name: str
    type: str
    status: str
    class Config:
        from_attributes = True

# -----------------------------------------------------
# Analytics & KPI Schemas
# -----------------------------------------------------
class KPICardOut(BaseModel):
    grid_power_kw: float
    voltage_v: float
    current_a: float
    power_factor: float
    transformer_load_pct: float
    frequency_hz: float
    energy_consumption_kwh: float
    running_furnace_count: int

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

class PredictionOut(BaseModel):
    time: datetime
    prediction_horizon_minutes: int
    sensor_id: int
    predicted_value: float
    upper_bound: Optional[float] = None
    lower_bound: Optional[float] = None
    class Config:
        from_attributes = True

class ReportOut(BaseModel):
    id: int
    created_at: datetime
    name: str
    report_type: str
    format: str
    file_path: str
    class Config:
        from_attributes = True
