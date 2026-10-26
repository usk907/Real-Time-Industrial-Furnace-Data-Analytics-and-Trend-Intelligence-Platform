"""
SQLAlchemy 2.0 ORM Models for Core Schema (Contract 1 <-> 2)
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    SmallInteger,
    String,
)
from sqlalchemy.sql import func

from server.app.database import Base


class FurnaceReading(Base):
    """Continuous time-series telemetry table."""

    __tablename__ = "furnace_readings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts = Column(DateTime(timezone=False), nullable=False, index=True)
    tag = Column(String(64), nullable=False, index=True)
    value = Column(Float, nullable=False)
    quality = Column(SmallInteger, default=1)


class FurnaceLatest(Base):
    """Latest value cache table for rapid reads and WebSocket broadcasts."""

    __tablename__ = "furnace_latest"

    tag = Column(String(64), primary_key=True)
    value = Column(Float, nullable=False)
    ts = Column(DateTime(timezone=False), nullable=False)


class User(Base):
    """Authentication and RBAC users table."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        Enum("admin", "manager", "engineer", "operator", "viewer", name="user_roles"),
        nullable=False,
        default="viewer",
    )
    created_at = Column(DateTime, server_default=func.now())


class Alarm(Base):
    """Industrial alarm event logs and acknowledgments."""

    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime(timezone=False), nullable=False, index=True)
    tag = Column(String(64), nullable=False, index=True)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(32), nullable=False, default="WARNING")
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_by = Column(String(64), nullable=True)
    resolved_at = Column(DateTime(timezone=False), nullable=True)
