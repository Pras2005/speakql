from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    # Base
    ENV: str = "dev"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/speakql"
    SQL_ECHO: bool = False
    
    # Auth
    JWT_SECRET_KEY: str = "supersecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # AI Providers
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    LOCAL_AI_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_AI_API_KEY: str = "ollama"
    OPENAI_API_KEY: Optional[str] = None
    
    # Encryption
    FERNET_KEY: str = "v6bWfPzX2U1h_P-K_rS6QoM6f0l_H5S_C7O8N9M0L1K=" # Default for dev
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
