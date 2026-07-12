"""
app/extensions.py — Flask extensions (SQLAlchemy db instance).

Import `db` from here in models and blueprints to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy

# We use flask-sqlalchemy for convenience in the Flask app context,
# but models.py also defines raw SQLAlchemy Table objects for reports-api.
# For the scaffold, we use a simple SQLAlchemy engine directly.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os


class Base(DeclarativeBase):
    pass


def get_engine(app=None):
    """Return a SQLAlchemy engine from Flask app config or env var."""
    url = (
        app.config["SQLALCHEMY_DATABASE_URI"]
        if app
        else os.getenv("DATABASE_URL", "postgresql+psycopg2://assetflow:assetflow_secret@localhost:5432/assetflow_db")
    )
    return create_engine(url, pool_pre_ping=True)


def get_session(engine):
    """Return a scoped session factory."""
    Session = sessionmaker(bind=engine)
    return Session()
