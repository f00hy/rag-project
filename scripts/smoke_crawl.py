"""Standalone script that replicates the crawl endpoint flow.

Usage:
    uv run python scripts/smoke_crawl.py <url> [--max-pages N]

Performs: crawl -> chunk -> embed -> index (object store, vector DB, relational DB).
"""

import argparse
import asyncio
import logging
import os
import time
from sys import stdout

from dotenv import load_dotenv
from pydantic import HttpUrl

load_dotenv()

os.environ["POSTGRES_URL"] = os.getenv("POSTGRES_URL_LOCAL", "sqlite+aiosqlite://")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(stdout)],
)
logger = logging.getLogger(__name__)


async def main(url: str, max_pages: int) -> None:
    """Run the full crawl-and-ingest pipeline for a given URL."""
    from app.infra.postgres import init_rel_db
    from app.infra.qdrant import init_vec_db
    from app.pipelines.ingestion import ingest
    from app.services.crawling import crawl

    logger.info("Initializing infrastructure...")
    await init_vec_db()
    await init_rel_db()

    pages_crawled = 0
    pages_failed = 0
    failures: list[dict[str, str | None]] = []
    start = time.perf_counter()

    logger.info("Starting crawl: url=%s max_pages=%d", url, max_pages)
    try:
        async for result in crawl(start_url=HttpUrl(url), max_pages=max_pages):
            if result.success:
                logger.info(
                    "[%d] Crawled: %s — ingesting...", pages_crawled + 1, result.url
                )
                await ingest(result)
                pages_crawled += 1
            else:
                pages_failed += 1
                failures.append({"url": result.url, "error": result.error_message})
                logger.warning("Failed: %s — %s", result.url, result.error_message)
    except Exception:
        logger.exception("Crawl run failed")

    elapsed = time.perf_counter() - start

    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    logger.info("URL:            %s", url)
    logger.info("Pages crawled:  %d", pages_crawled)
    logger.info("Pages failed:   %d", pages_failed)
    logger.info("Elapsed:        %.2fs", elapsed)
    if failures:
        logger.info("Failures:")
        for f in failures:
            logger.info("  - %s: %s", f["url"], f["error"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the crawl + ingest pipeline")
    parser.add_argument("url", help="Start URL to crawl")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum pages to crawl (default: 5)",
    )
    args = parser.parse_args()
    if args.max_pages <= 0:
        parser.error("--max-pages must be a positive integer")
    asyncio.run(main(args.url, args.max_pages))
