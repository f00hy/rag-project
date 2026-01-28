"""Data models for the RAG pipeline."""

from pydantic import BaseModel


class Chunk(BaseModel):
    """Text chunk with hierarchical parent-child relationships."""

    text: str
    chunk_id: str
    parent_id: str | None = None
    child_ids: list[str] = []
