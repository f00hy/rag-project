"""Tests for the web crawling service."""

from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import HttpUrl

from app.services.crawling import crawl


async def _fake_results(results):
    """Yield pre-built results as an async iterator."""
    for r in results:
        yield r


async def test_crawl_yields_all_results():
    """Every result from the underlying crawler is yielded."""
    fake = [
        MagicMock(success=True, url="https://example.com/p1"),
        MagicMock(success=True, url="https://example.com/p2"),
    ]
    mock_crawler = AsyncMock()
    mock_crawler.arun = AsyncMock(return_value=_fake_results(fake))
    mock_crawler.__aenter__.return_value = mock_crawler
    mock_crawler.__aexit__.return_value = None

    with patch("app.services.crawling.AsyncWebCrawler", return_value=mock_crawler):
        results = [r async for r in crawl(HttpUrl("https://example.com"), max_pages=10)]

    assert len(results) == 2
    assert all(r.success for r in results)


async def test_crawl_handles_failures_without_stopping():
    """Failed pages are yielded without interrupting iteration."""
    fake = [
        MagicMock(success=True, url="https://example.com/p1"),
        MagicMock(success=False, url="https://example.com/p2", error_message="timeout"),
        MagicMock(success=True, url="https://example.com/p3"),
    ]
    mock_crawler = AsyncMock()
    mock_crawler.arun = AsyncMock(return_value=_fake_results(fake))
    mock_crawler.__aenter__.return_value = mock_crawler
    mock_crawler.__aexit__.return_value = None

    with patch("app.services.crawling.AsyncWebCrawler", return_value=mock_crawler):
        results = [r async for r in crawl(HttpUrl("https://example.com"), max_pages=10)]

    assert len(results) == 3
    assert results[1].success is False


async def test_crawl_with_all_failures():
    """All-failure crawls still yield every result."""
    fake = [
        MagicMock(success=False, url="https://example.com/bad", error_message="500"),
    ]
    mock_crawler = AsyncMock()
    mock_crawler.arun = AsyncMock(return_value=_fake_results(fake))
    mock_crawler.__aenter__.return_value = mock_crawler
    mock_crawler.__aexit__.return_value = None

    with patch("app.services.crawling.AsyncWebCrawler", return_value=mock_crawler):
        results = [r async for r in crawl(HttpUrl("https://example.com"), max_pages=5)]

    assert len(results) == 1
    assert results[0].success is False
