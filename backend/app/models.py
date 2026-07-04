from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from backend.app.database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    permissions = Column(JSON, default=[])

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Plant(Base):
    __tablename__ = "plants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    location = Column(String(150))
    timezone = Column(String(50), default="UTC")
    description = Column(Text)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    description = Column(Text)

class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    rated_capacity = Column(Float, default=0.0)
    status = Column(String(20), default="STOPPED")

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    register_address = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False)
    nominal_min = Column(Float)
    nominal_max = Column(Float)
    serial_number = Column(String(100))
    firmware_version = Column(String(50))
    communication_status = Column(String(20), default="ONLINE")
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    installation_date = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    time = Column(DateTime(timezone=True), primary_key=True)
    sensor_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)
    value = Column(Float, nullable=False)
    quality = Column(String(20), default="GOOD")
    status = Column(String(20), default="OK")

class Alarm(Base):
    __tablename__ = "alarms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    sensor_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    alarm_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    trigger_value = Column(Float)
    status = Column(String(20), default="ACTIVE")
    acknowledged_by = Column(String(50))
    comments = Column(Text)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime(timezone=True), server_default=func.now())
    equipment_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    description = Column(Text)
    severity = Column(String(20), default="INFO")

class Prediction(Base):
    __tablename__ = "predictions"
    time = Column(DateTime(timezone=True), primary_key=True)
    prediction_horizon_minutes = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)
    predicted_value = Column(Float, nullable=False)
    upper_bound = Column(Float)
    lower_bound = Column(Float)

class KPIHistory(Base):
    __tablename__ = "kpi_history"
    time = Column(DateTime(timezone=True), primary_key=True)
    equipment_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"), primary_key=True)
    kpi_name = Column(String(50), primary_key=True)
    value = Column(Float, nullable=False)
    unit = Column(String(20))

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String(150), nullable=False)
    report_type = Column(String(20), nullable=False)
    format = Column(String(10), nullable=False)
    file_path = Column(String(255), nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))

class SystemSetting(Base):
    __tablename__ = "settings"
    key = Column(String(100), primary_key=True)
    value = Column(String(255), nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(20), default="INFO")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
