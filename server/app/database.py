"""
Database Connection & Session Management
SQLAlchemy 2.0 Engine with PyMySQL pooling connecting to MySQL as server_user.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from server.app.config import settings

# PyMySQL pool configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=15,
    max_overflow=25,
    pool_timeout=10,
    pool_recycle=1800,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session
)

Base = declarative_base()

def get_db():
    """FastAPI dependency for yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
