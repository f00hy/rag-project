"""Data models for the RAG pipeline."""

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, HttpUrl
from qdrant_client.models import SparseVector
from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, Relationship, SQLModel


class Chunk(BaseModel):
    """Text chunk with hierarchical parent-child relationships."""

    id: str
    text: str
    parent_id: str | None = None
    child_ids: list[str] = []


class Embedding(BaseModel):
    """Dense and sparse vector embeddings for a chunk."""

    chunk_id: str | None = None
    dense: list[float]
    sparse: SparseVector


class Document(SQLModel, table=True):
    """Document metadata with associated content and parent chunks."""

    id: UUID = Field(primary_key=True)
    title: str
    content_key: str
    content_hash: str
    source_url: HttpUrl
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    parent_chunks: list["ParentChunk"] = Relationship(
        back_populates="document", cascade_delete=True
    )


class ParentChunk(SQLModel, table=True):
    """Top-level chunk containing the full text of a document section."""

    __tablename__ = "parent_chunk"

    id: UUID = Field(primary_key=True)
    text: str = Field(sa_column=Column(Text))

    document_id: UUID = Field(foreign_key="document.id", ondelete="CASCADE", index=True)
    document: Document = Relationship(back_populates="parent_chunks")
