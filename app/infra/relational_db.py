"""Relational database connection and initialization for Supabase."""

from os import getenv
from sqlalchemy import Engine
from sqlmodel import create_engine, SQLModel
from app.models import (
    Document,
)  # https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/#sqlmodel-metadata-order-matters

engine: Engine = create_engine(getenv("SUPABASE_URL"))


def init_relational_db() -> None:
    """Create all database tables defined in SQLModel metadata."""
    SQLModel.metadata.create_all(engine)
