"""
app/db.py — Async SQLAlchemy engine + session factory for core-api.

Usage in route handlers:
    async def my_endpoint(db: AsyncSession = Depends(get_db)):
        ...
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ── Engine ─────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
)

# ── Session factory ────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative base ───────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """All SQLAlchemy models inherit from this base."""
    pass


# ── Dependency ─────────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
