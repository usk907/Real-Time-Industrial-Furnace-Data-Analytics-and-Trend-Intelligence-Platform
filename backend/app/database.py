from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings

database_url = settings.DATABASE_URL
engine = None

if "postgresql" in database_url:
    try:
        # Test PostgreSQL connection to check if it's online
        print(f"[DATABASE]: Testing connection to PostgreSQL at {database_url}...")
        temp_engine = create_engine(database_url, pool_pre_ping=True)
        # Try connecting with a 1-second timeout
        conn = temp_engine.connect()
        conn.close()
        engine = temp_engine
        print("[DATABASE]: Successfully connected to PostgreSQL.")
    except Exception as e:
        print(f"[DATABASE WARNING]: PostgreSQL is offline or unreachable: {e}")
        print("[DATABASE]: Falling back to local SQLite database (furnace.db) for zero-setup execution...")
        database_url = "sqlite:///./furnace.db"
        # check_same_thread=False is required for SQLite inside multi-threaded FastAPI apps
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency injection to provide database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
