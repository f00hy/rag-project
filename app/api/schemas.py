"""Request and response models for API routes."""

from pydantic import BaseModel, HttpUrl

from app.config import MAX_PAGES


class CrawlRequest(BaseModel):
    """Request body for POST /crawl."""

    url: HttpUrl
    max_pages: int = MAX_PAGES


class CrawlFailure(BaseModel):
    """Single page crawl failure."""

    url: HttpUrl
    error_msg: str | None = None


class CrawlResponse(BaseModel):
    """Response for POST /crawl."""

    url: HttpUrl
    pages_crawled: int
    failures: list[CrawlFailure] = []
    run_error_msg: str | None = None
