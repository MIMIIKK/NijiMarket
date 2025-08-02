from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:Sabina123@localhost/nijimarket_db"
    
    # Security
    SECRET_KEY: str = "ql_u2NbJ625dofsfdKcyrvFjrz5d4e2qImtCS-jIKIU"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    APP_NAME: str = "NijiMarket"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:19006"]
    
    class Config:
        env_file = ".env"

settings = Settings()