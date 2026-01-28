"""Data models for the RAG pipeline."""

from pydantic import BaseModel
from dataclasses import dataclass
from fastembed import SparseEmbedding
from fastembed.common.types import NumpyArray


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
