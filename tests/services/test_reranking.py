"""Tests for the cross-encoder reranking service."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.models import ParentChunk
from app.services.reranking import rerank


async def test_rerank_returns_top_k_sorted(monkeypatch):
    """Chunks are returned in descending score order, limited to top-k."""
    chunks = [
        ParentChunk(id=uuid4(), text="chunk A", document_id=uuid4()),
        ParentChunk(id=uuid4(), text="chunk B", document_id=uuid4()),
        ParentChunk(id=uuid4(), text="chunk C", document_id=uuid4()),
        ParentChunk(id=uuid4(), text="chunk D", document_id=uuid4()),
    ]
    mock_encoder = MagicMock()
    mock_encoder.rerank.return_value = [0.1, 0.9, 0.5, 0.3]
    monkeypatch.setattr("app.services.reranking._cross_encoder", mock_encoder)

    result = await rerank("test query", chunks)

    assert len(result) <= 3
    assert result[0].text == "chunk B"


async def test_rerank_fewer_than_top_k(monkeypatch):
    """When fewer chunks than top-k are provided, all are returned."""
    chunks = [
        ParentChunk(id=uuid4(), text="only chunk", document_id=uuid4()),
    ]
    mock_encoder = MagicMock()
    mock_encoder.rerank.return_value = [0.5]
    monkeypatch.setattr("app.services.reranking._cross_encoder", mock_encoder)

    result = await rerank("query", chunks)
    assert len(result) == 1
    assert result[0].text == "only chunk"


async def test_rerank_preserves_chunk_identity(monkeypatch):
    """Returned chunks are the same objects as the input chunks."""
    chunks = [
        ParentChunk(id=uuid4(), text="alpha", document_id=uuid4()),
        ParentChunk(id=uuid4(), text="beta", document_id=uuid4()),
    ]
    mock_encoder = MagicMock()
    mock_encoder.rerank.return_value = [0.3, 0.7]
    monkeypatch.setattr("app.services.reranking._cross_encoder", mock_encoder)

    result = await rerank("q", chunks)

    assert result[0] is chunks[1]
    assert result[1] is chunks[0]
