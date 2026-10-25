"""
Pydantic Request & Response Schemas
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- Auth Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# --- Health Schema ---
class HealthResponse(BaseModel):
    status: str
    db_ok: bool
    server_time: str

# --- Live Telemetry Schemas ---
class TagLiveItem(BaseModel):
    tag: str
    value: float
    unit: str
    ts: datetime
    status: str  # "NORMAL", "WARNING", "CRITICAL"
    equipment: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None

class LiveResponse(BaseModel):
    ts: datetime
    tags: List[TagLiveItem]

# --- History Schemas ---
class HistoryPoint(BaseModel):
    ts: datetime
    value: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    count: Optional[int] = None

class HistoryResponse(BaseModel):
    tag: str
    bucket: str
    from_ts: datetime
    to_ts: datetime
    count: int
    points: List[HistoryPoint]

# --- Alarms Schemas ---
class AlarmOut(BaseModel):
    id: int
    ts: datetime
    tag: str
    value: float
    threshold: float
    severity: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AlarmAckResponse(BaseModel):
    success: bool
    id: int
    acknowledged_by: str
    status: str
