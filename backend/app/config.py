from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Real-Time Industrial Furnace Data Analytics and Trend Intelligence Platform"
    API_V1_STR: str = "/api"
    
    # Database Settings
    # Defaulting to local postgresql if not specified. If running in docker, docker-compose overrides it to 'timescaledb'
    DATABASE_URL: str = "postgresql://admin:securepassword@localhost:5432/furnace_db"
    
    # Security Settings
    SECRET_KEY: str = "SUPER_SECRET_INDUSTRIAL_KEY_9812A7C"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours shift duration
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
