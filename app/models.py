"""Data models for the RAG pipeline."""

from __future__ import annotations
from pydantic import BaseModel
from qdrant_client.models import SparseVector
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, Text
from uuid import UUID, uuid4
from datetime import datetime, timezone


class Chunk(BaseModel):
    """Text chunk with hierarchical parent-child relationships."""

    id: str
    text: str
    parent_id: str | None = None
    child_ids: list[str] = []


class Embedding(BaseModel):
    """Dense and sparse vector embeddings for a chunk."""

    chunk_id: str
    dense_embedding: list[float]
    sparse_embedding: SparseVector


class Document(SQLModel, table=True):
    """Document metadata with associated content and parent chunks."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    content_key: str
    source_url: str
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    content_hash: str

    parent_chunks: list[ParentChunk] = Relationship(
        back_populates="document", cascade_delete=True
    )


class ParentChunk(SQLModel, table=True):
    """Top-level chunk containing the full text of a document section."""

    __tablename__ = "parent_chunk"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    text: str = Field(sa_column=Column(Text))

    document_id: UUID = Field(foreign_key="document.id", ondelete="CASCADE", index=True)
    document: Document = Relationship(back_populates="parent_chunks")
