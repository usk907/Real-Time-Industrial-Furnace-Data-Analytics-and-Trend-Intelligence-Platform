from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings

database_url = settings.DATABASE_URL
engine = None

if "postgresql" in database_url or "mysql" in database_url:
    try:
        # Test connection to check if it's online
        print(f"[DATABASE]: Testing connection to database at {database_url}...")
        temp_engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=25,
            max_overflow=50,
            pool_timeout=10,
            pool_recycle=1800
        )
        conn = temp_engine.connect()
        conn.close()
        engine = temp_engine
        print("[DATABASE]: Successfully connected to database.")
    except Exception as e:
        print(f"[DATABASE WARNING]: Remote database is offline or unreachable: {e}")
        print("[DATABASE]: Falling back to local SQLite database (furnace.db) for zero-setup execution...")
        database_url = "sqlite:///./furnace.db"
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
