"""Relational database connection and initialization for Supabase."""

from os import getenv
from sqlalchemy import Engine
from sqlmodel import create_engine, SQLModel
from app.models import (
    Document,  # noqa: F401
    ParentChunk,  # noqa: F401
)  # Imports needed for SQLModel metadata registration

rel_db_engine: Engine = create_engine(getenv("SUPABASE_URL", "sqlite://"))


def init_rel_db() -> None:
    """Create all database tables defined in SQLModel metadata."""
    SQLModel.metadata.create_all(rel_db_engine)
