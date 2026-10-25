from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv
import os

# Load environment variables from .env file
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Industrial Energy Intelligence Platform (IEIP)"
    API_V1_STR: str = "/api"
    
    # PostgreSQL Settings
    DATABASE_URL: str = "postgresql://admin:securepassword@localhost:5432/furnace_db"
    
    # InfluxDB Settings
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "my-super-secret-admin-token-1234567890"
    INFLUXDB_ORG: str = "ieip_org"
    INFLUXDB_BUCKET: str = "furnace_telemetry"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security Settings
    SECRET_KEY: str = "SUPER_SECRET_INDUSTRIAL_KEY_9812A7C"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours shift duration
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
