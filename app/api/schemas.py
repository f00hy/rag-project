"""Request and response models for API routes."""

from uuid import UUID

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


class QueryRequest(BaseModel):
    """Request body for POST /query."""

    query: str


class QueryContextChunk(BaseModel):
    """Retrieved context chunk used to generate an answer."""

    id: UUID
    text: str


class QueryCitation(BaseModel):
    """Citation metadata associated with retrieved context."""

    parent_chunk_id: UUID
    document_id: UUID | None = None
    source_url: HttpUrl | None = None


class QueryResponse(BaseModel):
    """Response for POST /query."""

    query: str
    answer: str
    context_chunks: list[QueryContextChunk] = []
    citations: list[QueryCitation] = []
    run_error_msg: str | None = None
