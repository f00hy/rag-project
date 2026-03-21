"""Tests for the data ingestion pipeline."""

from hashlib import sha256
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import models
from sqlmodel import select

from app.config import COLLECTION_NAME
from app.models import Chunk, Document, Embedding, ParentChunk
from app.pipelines.ingestion import ingest
from tests.constants import DENSE_DIM

DIVERSE_CONTENT = """\
# Data Engineering Fundamentals

Data engineering involves designing, building, and maintaining infrastructure
for large-scale data processing. Engineers create robust pipelines that transform
raw information into structured formats suitable for analytics and machine learning
applications across distributed computing environments.

## Storage Architecture

Modern data platforms employ tiered storage strategies combining object stores
for raw archives, columnar databases for analytical queries, and key-value caches
for low-latency access patterns. Schema evolution and data governance policies
ensure consistency across organizational boundaries.
"""


def _make_crawl_result(
    url="https://example.com/page", title="Test Page", content=DIVERSE_CONTENT
):
    """Build a fake CrawlResult with the fields accessed by ingest()."""
    result = MagicMock()
    result.url = url
    result.metadata = {"title": title}
    result.markdown = MagicMock()
    result.markdown.fit_markdown = content
    result.success = True
    return result


def _fake_chunks():
    """Return deterministic parent/child chunks."""
    parents = [
        Chunk(id="p_0", text="parent text zero", child_ids=["c_0", "c_1"]),
        Chunk(id="p_1", text="parent text one", child_ids=["c_2"]),
    ]
    children = [
        Chunk(id="c_0", text="child text zero", parent_id="p_0"),
        Chunk(id="c_1", text="child text one", parent_id="p_0"),
        Chunk(id="c_2", text="child text two", parent_id="p_1"),
    ]
    return parents, children


def _fake_embeddings(children):
    """Return deterministic embeddings matching the children."""
    return [
        Embedding(
            chunk_id=c.id,
            dense=[0.1 * (i + 1)] * DENSE_DIM,
            sparse=models.SparseVector(indices=[0, 1], values=[0.5, 0.3]),
        )
        for i, c in enumerate(children)
    ]


async def test_ingest_stores_across_all_backends(
    monkeypatch, patch_vec_db, patch_rel_db, patch_obj_store, vec_db, rel_db, obj_store
):
    """ingest() stores data in R2, Qdrant, and PostgreSQL."""
    parents, children = _fake_chunks()
    monkeypatch.setattr(
        "app.pipelines.ingestion.chunk",
        AsyncMock(return_value=(parents, children)),
    )
    monkeypatch.setattr(
        "app.pipelines.ingestion.embed_chunks",
        AsyncMock(return_value=_fake_embeddings(children)),
    )

    result = _make_crawl_result()
    await ingest(result)

    assert len(obj_store.objects) == 1

    info = await vec_db.get_collection(COLLECTION_NAME)
    assert info.points_count == len(children)

    async with rel_db() as session:
        docs = (await session.exec(select(Document))).all()
        assert len(docs) == 1
        chunks = (await session.exec(select(ParentChunk))).all()
        assert len(chunks) == len(parents)


async def test_ingest_skips_unchanged_content(monkeypatch, patch_rel_db, rel_db):
    """Unchanged content (same hash) is skipped without re-indexing."""
    result = _make_crawl_result()
    parsed_url = urlparse(result.url)
    content_key = f"{parsed_url.netloc}{parsed_url.path}".replace("/", "_")
    content_hash = sha256(DIVERSE_CONTENT.encode("utf-8")).hexdigest()

    doc = Document(
        id=uuid5(NAMESPACE_URL, content_key),
        title="Existing",
        content_key=content_key,
        content_hash=content_hash,
        source_url=result.url,
    )
    async with rel_db() as session:
        session.add(doc)
        await session.commit()

    mock_chunk = AsyncMock()
    mock_embed = AsyncMock()
    monkeypatch.setattr("app.pipelines.ingestion.chunk", mock_chunk)
    monkeypatch.setattr("app.pipelines.ingestion.embed_chunks", mock_embed)

    await ingest(result)

    mock_chunk.assert_not_called()
    mock_embed.assert_not_called()


async def test_ingest_skips_empty_content(monkeypatch):
    """Empty markdown content is skipped early."""
    mock_chunk = AsyncMock()
    monkeypatch.setattr("app.pipelines.ingestion.chunk", mock_chunk)

    result = _make_crawl_result(content="")
    await ingest(result)

    mock_chunk.assert_not_called()
