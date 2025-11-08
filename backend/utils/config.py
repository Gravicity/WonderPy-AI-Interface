"""
Configuration Management
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Application Settings
    APP_NAME: str = "WonderPy AI Interface"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "postgresql://wonderpy:password@localhost:5432/wonderpy_db"
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Services
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Voice Services
    ELEVENLABS_API_KEY: str = ""
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"

    # Robot Settings
    ROBOT_SCAN_TIMEOUT: int = 20
    ROBOT_CONNECTION_TIMEOUT: int = 30
    SENSOR_UPDATE_RATE_HZ: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string if needed"""
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                return [self.CORS_ORIGINS]
        return self.CORS_ORIGINS


# Global settings instance
settings = Settings()
