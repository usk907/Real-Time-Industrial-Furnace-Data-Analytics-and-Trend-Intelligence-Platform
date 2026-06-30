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
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Area(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    description = Column(Text)

class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True, index=True)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(20), default="STOPPED")

class Sensor(Base):
    __tablename__ = "sensors"
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    register_address = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False)
    nominal_min = Column(Float)
    nominal_max = Column(Float)
    is_active = Column(Boolean, default=True)

# -----------------------------------------------------
# Time-Series Models (hypertables if PostgreSQL/TimescaleDB)
# -----------------------------------------------------
class SensorReading(Base):
    __tablename__ = "sensor_readings"
    time = Column(DateTime(timezone=True), primary_key=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), primary_key=True)
    value = Column(Float, nullable=False)
    quality = Column(String(20), default="GOOD")
    status = Column(String(20), default="OK")

class Alarm(Base):
    __tablename__ = "alarms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime(timezone=True), primary_key=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)
    alarm_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    trigger_value = Column(Float)
    status = Column(String(20), default="ACTIVE")
    acknowledged_by = Column(String(50))
    comments = Column(Text)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime(timezone=True), primary_key=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    description = Column(Text)
    severity = Column(String(20), default="INFO")

class Prediction(Base):
    __tablename__ = "predictions"
    time = Column(DateTime(timezone=True), primary_key=True)
    prediction_horizon_minutes = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), primary_key=True)
    predicted_value = Column(Float, nullable=False)
    upper_bound = Column(Float)
    lower_bound = Column(Float)

class KPIHistory(Base):
    __tablename__ = "kpi_history"
    time = Column(DateTime(timezone=True), primary_key=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), primary_key=True)
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
