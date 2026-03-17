"""Tests for the retrieval pipeline."""

from unittest.mock import AsyncMock
from uuid import uuid4

from qdrant_client.models import SparseVector

from app.models import Document, Embedding, ParentChunk
from app.pipelines.retrieval import retrieve
from tests.constants import DENSE_DIM


def _fake_embedding():
    """Return a deterministic Embedding for query tests."""
    return Embedding(
        dense=[0.1] * DENSE_DIM,
        sparse=SparseVector(indices=[0], values=[1.0]),
    )


async def test_retrieve_full_pipeline(monkeypatch, patch_rel_db, rel_db):
    """retrieve() chains embed -> search -> fetch -> rerank."""
    parent_id = uuid4()
    doc_id = uuid4()

    doc = Document(
        id=doc_id,
        title="T",
        content_key="k",
        content_hash="h",
        source_url="https://example.com",
    )
    pc = ParentChunk(id=parent_id, text="relevant text", document=doc)
    async with rel_db() as session:
        session.add(doc)
        session.add(pc)
        await session.commit()

    monkeypatch.setattr(
        "app.pipelines.retrieval.embed_query",
        AsyncMock(return_value=_fake_embedding()),
    )
    monkeypatch.setattr(
        "app.pipelines.retrieval.search",
        AsyncMock(return_value=[parent_id]),
    )
    monkeypatch.setattr(
        "app.pipelines.retrieval.rerank",
        AsyncMock(side_effect=lambda q, chunks: chunks),
    )

    result = await retrieve("test query")

    assert len(result) == 1
    assert result[0].text == "relevant text"


async def test_retrieve_no_results(monkeypatch):
    """Returns an empty list when search finds nothing."""
    monkeypatch.setattr(
        "app.pipelines.retrieval.embed_query",
        AsyncMock(return_value=_fake_embedding()),
    )
    mock_search = AsyncMock(return_value=[])
    monkeypatch.setattr("app.pipelines.retrieval.search", mock_search)
    mock_rerank = AsyncMock()
    monkeypatch.setattr("app.pipelines.retrieval.rerank", mock_rerank)

    result = await retrieve("no results query")

    assert result == []
    mock_rerank.assert_not_awaited()


async def test_retrieve_warns_on_missing_chunks(monkeypatch, patch_rel_db, rel_db):
    """A warning-level path is hit when DB returns fewer chunks than expected."""
    missing_id = uuid4()
    monkeypatch.setattr(
        "app.pipelines.retrieval.embed_query",
        AsyncMock(return_value=_fake_embedding()),
    )
    monkeypatch.setattr(
        "app.pipelines.retrieval.search",
        AsyncMock(return_value=[missing_id]),
    )
    monkeypatch.setattr(
        "app.pipelines.retrieval.rerank",
        AsyncMock(side_effect=lambda q, chunks: chunks),
    )

    result = await retrieve("query for missing chunks")
    assert result == []
