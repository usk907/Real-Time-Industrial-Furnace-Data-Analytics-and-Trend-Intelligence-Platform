import os
from pydantic_settings import BaseSettings

class TapSettings(BaseSettings):
    TAP_SERVER_HOST: str = os.getenv("TAP_SERVER_HOST", "127.0.0.1")
    TAP_SERVER_PORT: int = int(os.getenv("TAP_SERVER_PORT", "8001"))
    
    # SQL Database URL - defaults to SQLite tap_data.db or inherits existing SQL DB
    TAP_DATABASE_URL: str = os.getenv(
        "TAP_DATABASE_URL", 
        os.getenv("DATABASE_URL", "sqlite:///./tap_data.db")
    )
    
    # Ingestion Buffer Configuration
    BATCH_SIZE: int = 100
    FLUSH_INTERVAL_SECONDS: float = 0.5
    
    class Config:
        case_sensitive = True

tap_settings = TapSettings()
