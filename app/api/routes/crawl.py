"""Crawl API router."""

from fastapi import APIRouter
from pydantic import HttpUrl

from app.api.schemas import CrawlFailure, CrawlRequest, CrawlResponse
from app.pipelines.ingestion import ingest
from app.services.crawling import crawl

router = APIRouter(prefix="/crawl", tags=["crawl"])


@router.post("/", response_model=CrawlResponse)
async def crawl_endpoint(request: CrawlRequest) -> CrawlResponse:
    """Crawl pages starting from the given URL and ingest successful results.

    Args:
        request: Parameters for the crawl, including the start URL and
            maximum number of pages to crawl.

    Returns:
        A `CrawlResponse` containing crawl statistics, any per-page failures,
        and an optional top-level error message.
    """
    pages_crawled = 0
    failures: list[CrawlFailure] = []
    run_error_msg = None

    try:
        async for result in crawl(start_url=request.url, max_pages=request.max_pages):
            if result.success:
                await ingest(result)
                pages_crawled += 1
            else:
                failures.append(
                    CrawlFailure(
                        url=HttpUrl(result.url), error_msg=result.error_message
                    )
                )
    except Exception as e:
        run_error_msg = str(e)

    return CrawlResponse(
        url=request.url,
        pages_crawled=pages_crawled,
        failures=failures,
        run_error_msg=run_error_msg,
    )
