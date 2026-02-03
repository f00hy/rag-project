"""Data models for the RAG pipeline."""

from __future__ import annotations
from pydantic import BaseModel
from dataclasses import dataclass
from fastembed import SparseEmbedding
from fastembed.common.types import NumpyArray
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text
from uuid import UUID, uuid4
from datetime import datetime, timezone


class Chunk(BaseModel):
    """Text chunk with hierarchical parent-child relationships."""

    text: str
    chunk_id: str
    parent_id: str | None = None
    child_ids: list[str] = []


@dataclass
class Embedding:
    """Dense and sparse vector embeddings for a chunk."""

    chunk_id: str
    dense_embedding: NumpyArray
    sparse_embedding: SparseEmbedding


class Document(SQLModel, table=True):
    """Document metadata with associated content and parent chunks."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    content_key: str
    source_url: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
