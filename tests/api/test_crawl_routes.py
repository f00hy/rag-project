"""Tests for the crawl API endpoint."""

from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.routes.crawl import router

_app = FastAPI()
_app.include_router(router)


async def _fake_results(results):
    """Yield pre-built results as an async iterator."""
    for r in results:
        yield r


async def test_crawl_endpoint_success(monkeypatch):
    """Successful crawl returns pages_crawled and no failures."""
    mock_results = [
        MagicMock(success=True, url="https://example.com/p1"),
        MagicMock(success=True, url="https://example.com/p2"),
    ]

    async def fake_crawl(**kwargs):
        for r in mock_results:
            yield r

    monkeypatch.setattr("app.api.routes.crawl.crawl", fake_crawl)
    monkeypatch.setattr("app.api.routes.crawl.ingest", AsyncMock())

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/crawl/", json={"url": "https://example.com", "max_pages": 5}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["pages_crawled"] == 2
    assert data["failures"] == []
    assert data["run_error_msg"] is None


async def test_crawl_endpoint_respects_max_pages(monkeypatch):
    """Only the first max_pages successful results are ingested when the crawler yields more."""
    mock_results = [
        MagicMock(success=True, url="https://example.com/p1"),
        MagicMock(success=True, url="https://example.com/p2"),
        MagicMock(success=True, url="https://example.com/p3"),
        MagicMock(success=True, url="https://example.com/p4"),
    ]

    async def fake_crawl(**kwargs):
        for r in mock_results:
            yield r

    ingest_mock = AsyncMock()
    monkeypatch.setattr("app.api.routes.crawl.crawl", fake_crawl)
    monkeypatch.setattr("app.api.routes.crawl.ingest", ingest_mock)

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/crawl/", json={"url": "https://example.com", "max_pages": 3}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["pages_crawled"] == 3
    assert ingest_mock.call_count == 3


async def test_crawl_endpoint_with_failures(monkeypatch):
    """Failed pages appear in the failures list."""
    mock_results = [
        MagicMock(success=True, url="https://example.com/ok"),
        MagicMock(success=False, url="https://example.com/bad", error_message="500"),
    ]

    async def fake_crawl(**kwargs):
        for r in mock_results:
            yield r

    monkeypatch.setattr("app.api.routes.crawl.crawl", fake_crawl)
    monkeypatch.setattr("app.api.routes.crawl.ingest", AsyncMock())

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/crawl/", json={"url": "https://example.com"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["pages_crawled"] == 1
    assert len(data["failures"]) == 1
    assert data["failures"][0]["error_msg"] == "500"


async def test_crawl_endpoint_captures_exception(monkeypatch):
    """Top-level exceptions are captured in run_error_msg."""

    def failing_crawl(**kwargs):
        raise RuntimeError("crawler crashed")

    monkeypatch.setattr("app.api.routes.crawl.crawl", failing_crawl)
    monkeypatch.setattr("app.api.routes.crawl.ingest", AsyncMock())

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/crawl/", json={"url": "https://example.com"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["pages_crawled"] == 0
    assert data["run_error_msg"] == "crawler crashed"
