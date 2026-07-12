"""
app/core/config.py — Pydantic-Settings configuration for core-api.
Reads values from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://assetflow:assetflow_secret@localhost:5432/assetflow_db"

    # JWT (shared secret with reports-api)
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "AssetFlow Core API"
    API_V1_PREFIX: str = "/api"


settings = Settings()
