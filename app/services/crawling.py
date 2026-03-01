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

strategy = BFSDeepCrawlStrategy(
    max_depth=3,
    include_external=False,
    max_pages=100,
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


async def crawl(start_url: str) -> AsyncGenerator[CrawlResult]:
    """Deep-crawl a site via BFS starting from the given URL.

    Args:
        start_url: Root URL to begin crawling from.

    Yields:
        CrawlResult: Successfully crawled page results.
    """
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
                yield result
            else:
                logger.warning(
                    "Failed to crawl %s: %s", result.url, result.error_message
                )
    logger.info("Crawl finished — %d pages crawled successfully", page_count)
