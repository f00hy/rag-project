"""Tests for the embedding service (dense + sparse)."""

from unittest.mock import MagicMock

import numpy as np

from app.models import Chunk
from app.services.embedding import embed_chunks, embed_query
from tests.constants import DENSE_DIM


def _fake_sparse_result():
    """Return a mock sparse embedding with deterministic indices/values."""
    mock = MagicMock()
    mock.indices = MagicMock()
    mock.indices.tolist.return_value = [0, 5, 10]
    mock.values = MagicMock()
    mock.values.tolist.return_value = [0.5, 0.3, 0.8]
    return mock


async def test_embed_chunks_returns_correct_count(monkeypatch):
    """One Embedding is returned per input chunk."""
    chunks = [
        Chunk(id="c_0", text="Distributed systems rely on consensus algorithms"),
        Chunk(id="c_1", text="Neural architecture search automates model design"),
        Chunk(id="c_2", text="Gradient descent optimizes differentiable objectives"),
    ]
    dense_model = MagicMock()
    dense_model.embed.return_value = [
        np.random.default_rng(i).random(DENSE_DIM).astype(np.float32)
        for i in range(len(chunks))
    ]
    sparse_model = MagicMock()
    sparse_model.embed.return_value = [_fake_sparse_result() for _ in chunks]

    monkeypatch.setattr("app.services.embedding._dense_model", dense_model)
    monkeypatch.setattr("app.services.embedding._sparse_model", sparse_model)

    embeddings = await embed_chunks(chunks)

    assert len(embeddings) == 3
    for emb in embeddings:
        assert len(emb.dense) == DENSE_DIM
        assert emb.sparse.indices == [0, 5, 10]


async def test_embed_chunks_preserves_chunk_ids(monkeypatch):
    """Each returned Embedding carries the corresponding chunk_id."""
    chunks = [
        Chunk(id="c_0", text="Information retrieval fundamentals"),
        Chunk(id="c_1", text="Probabilistic graphical models overview"),
    ]
    dense_model = MagicMock()
    dense_model.embed.return_value = [
        np.zeros(DENSE_DIM, dtype=np.float32) for _ in chunks
    ]
    sparse_model = MagicMock()
    sparse_model.embed.return_value = [_fake_sparse_result() for _ in chunks]

    monkeypatch.setattr("app.services.embedding._dense_model", dense_model)
    monkeypatch.setattr("app.services.embedding._sparse_model", sparse_model)

    embeddings = await embed_chunks(chunks)
    assert [e.chunk_id for e in embeddings] == ["c_0", "c_1"]


async def test_embed_query_returns_single_embedding(monkeypatch):
    """embed_query returns a single Embedding with no chunk_id."""
    dense_model = MagicMock()
    dense_model.query_embed.return_value = [
        np.random.default_rng(42).random(DENSE_DIM).astype(np.float32)
    ]
    sparse_model = MagicMock()
    sparse_model.query_embed.return_value = [_fake_sparse_result()]

    monkeypatch.setattr("app.services.embedding._dense_model", dense_model)
    monkeypatch.setattr("app.services.embedding._sparse_model", sparse_model)

    embedding = await embed_query("test query about language models")

    assert len(embedding.dense) == DENSE_DIM
    assert embedding.chunk_id is None
    assert embedding.sparse.indices == [0, 5, 10]
