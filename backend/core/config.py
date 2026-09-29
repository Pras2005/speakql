import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

logger = logging.getLogger(__name__)

# Insecure default sentinel values — must be overridden in production
_INSECURE_JWT_DEFAULT = "supersecret"
_INSECURE_FERNET_DEFAULT = "v6bWfPzX2U1h_P-K_rS6QoM6f0l_H5S_C7O8N9M0L1K="


class Settings(BaseSettings):
    # Base
    ENV: str = "dev"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/speakql"
    SQL_ECHO: bool = False

    # Auth
    JWT_SECRET_KEY: str = _INSECURE_JWT_DEFAULT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # AI Providers
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    LOCAL_AI_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_AI_API_KEY: str = "ollama"
    OPENAI_API_KEY: Optional[str] = None

    # Encryption
    FERNET_KEY: str = _INSECURE_FERNET_DEFAULT  # MUST be overridden in production

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def validate_security(self) -> None:
        """
        Logs critical security warnings if insecure defaults are in use.
        Should be called at application startup.
        In non-dev environments these warnings become errors.
        """
        issues = []

        if self.JWT_SECRET_KEY == _INSECURE_JWT_DEFAULT:
            issues.append("JWT_SECRET_KEY is using the insecure default value")

        if self.FERNET_KEY == _INSECURE_FERNET_DEFAULT:
            issues.append("FERNET_KEY is using the insecure default value")

        if issues:
            msg = "SECURITY WARNING: %s. Set these via environment variables or .env file."
            issues_str = "; ".join(issues)
            if self.ENV in ("prod", "production", "staging"):
                # Crash fast in production rather than expose insecure defaults
                raise RuntimeError(
                    f"[FATAL] Refusing to start in '{self.ENV}' environment with insecure defaults. "
                    f"{issues_str}"
                )
            else:
                logger.warning(msg, issues_str)


settings = Settings()
