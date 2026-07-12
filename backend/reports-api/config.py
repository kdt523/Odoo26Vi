"""
config.py — Environment-driven configuration for reports-api.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Database — sync psycopg2 URL (reports-api reads only)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://assetflow:assetflow_secret@localhost:5432/assetflow_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Shared JWT secret — MUST match core-api's JWT_SECRET
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    # Flask
    SECRET_KEY = os.getenv("JWT_SECRET", "change-me")
    DEBUG = os.getenv("ENVIRONMENT", "development") == "development"


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": Config,
    "production": ProductionConfig,
}
