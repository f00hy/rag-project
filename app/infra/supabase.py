"""Relational database connection and initialization for Supabase."""

from os import getenv
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from app.models import (
    Document,  # noqa: F401
    ParentChunk,  # noqa: F401
)  # Imports needed for SQLModel metadata registration

_engine: AsyncEngine = create_async_engine(
    getenv("SUPABASE_URL", "sqlite+aiosqlite://")
)

rel_db_session = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)


async def init_rel_db() -> None:
    """Create all database tables defined in SQLModel metadata."""
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
