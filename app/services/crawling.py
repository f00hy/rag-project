"""Web crawling service using crawl4ai for deep site crawling."""

import logging
from collections.abc import AsyncGenerator

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    CrawlResult,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from pydantic import HttpUrl

from app.config import MAX_PAGES

logger = logging.getLogger(__name__)

browser_config = BrowserConfig(headless=True, verbose=False)

md_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(),
    options={
        "include_sup_sub": True,
        "skip_internal_links": True,
        "images_to_alt": True,
    },
)


def _make_strategy_and_config(
    max_pages: int,
) -> tuple[BFSDeepCrawlStrategy, CrawlerRunConfig]:
    """Build crawl strategy and run config for crawling.

    Args:
        max_pages: Maximum number of pages to crawl.

    Returns:
        A tuple containing:
        - BFSDeepCrawlStrategy: The configured deep crawl strategy.
        - CrawlerRunConfig: The run configuration using that strategy.
    """
    strategy = BFSDeepCrawlStrategy(
        max_depth=3,
        include_external=False,
        max_pages=max_pages,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=30000,  # 30 seconds
        remove_overlay_elements=True,
        exclude_external_links=True,
        preserve_https_for_internal_links=True,
        check_robots_txt=True,
        markdown_generator=md_generator,
        deep_crawl_strategy=strategy,
        stream=True,
    )
    return strategy, run_config


async def crawl(
    start_url: HttpUrl,
    max_pages: int = MAX_PAGES,
) -> AsyncGenerator[CrawlResult]:
    """Deep-crawl a site via BFS starting from the given URL.

    Args:
        start_url: Root URL to begin crawling from.
        max_pages: Per-crawl page limit.

    Yields:
        CrawlResult: Per-page crawl results.
    """
    strategy, run_config = _make_strategy_and_config(max_pages)
    logger.info(
        "Starting BFS crawl from %s (max_depth=%d, max_pages=%d)",
        start_url,
        strategy.max_depth,
        strategy.max_pages,
    )
    page_count = 0
    async with AsyncWebCrawler(config=browser_config) as crawler:
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                page_count += 1
                logger.debug("Crawled page %d: %s", page_count, result.url)
            else:
                logger.warning(
                    "Failed to crawl %s: %s", result.url, result.error_message
                )
            yield result
    logger.debug("Crawl finished — %d pages crawled successfully", page_count)
