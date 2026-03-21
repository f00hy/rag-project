"""Relational database connection and initialization for PostgreSQL."""

import logging
from os import getenv

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    Document,  # noqa: F401
    ParentChunk,  # noqa: F401
)  # Imports needed for SQLModel metadata registration

logger = logging.getLogger(__name__)

_engine: AsyncEngine = create_async_engine(
    getenv("POSTGRES_URL", "sqlite+aiosqlite://")
)

rel_db_session = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)


async def init_rel_db() -> None:
    """Create all database tables defined in SQLModel metadata."""
    logger.info("Initializing relational database tables")
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.debug("Relational database tables created successfully")
