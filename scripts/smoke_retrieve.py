"""Standalone script that replicates the retrieval pipeline flow.

Usage:
    uv run python scripts/smoke_retrieve.py "<query>" [--limit N]

Performs: embed query -> search -> fetch -> rerank.
"""

import argparse
import asyncio
import logging
import os
import time
from sys import stdout
from uuid import UUID

from dotenv import load_dotenv

load_dotenv()

os.environ["POSTGRES_URL"] = os.getenv("POSTGRES_URL_LOCAL", "sqlite+aiosqlite://")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(stdout)],
)
logger = logging.getLogger(__name__)


def _format_chunk_preview(chunk_text: str, max_chars: int = 120) -> str:
    """Return a single-line preview for chunk text."""
    normalized = " ".join(chunk_text.split())
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 3]}..."


def _format_chunk_id(chunk_id: UUID | str | None) -> str:
    """Format chunk IDs safely for logs."""
    if chunk_id is None:
        return "N/A"
    return str(chunk_id)


async def main(query: str, limit: int) -> None:
    """Run the retrieval pipeline for a given query."""
    from app.infra.postgres import init_rel_db
    from app.infra.qdrant import init_vec_db
    from app.pipelines.retrieval import retrieve

    logger.info("Initializing infrastructure...")
    await init_vec_db()
    await init_rel_db()

    start = time.perf_counter()
    chunks = []

    logger.info("Starting retrieval: query=%s", query)
    try:
        chunks = await retrieve(query)
    except Exception:
        logger.exception("Retrieval run failed")

    elapsed = time.perf_counter() - start
    shown_chunks = chunks[:limit]

    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    logger.info("Query:          %s", query)
    logger.info("Chunks found:   %d", len(chunks))
    logger.info("Chunks shown:   %d (limit=%d)", len(shown_chunks), limit)
    logger.info("Elapsed:        %.2fs", elapsed)

    if shown_chunks:
        logger.info("Top chunks:")
        for index, chunk in enumerate(shown_chunks, start=1):
            chunk_id = _format_chunk_id(getattr(chunk, "id", None))
            chunk_text = getattr(chunk, "text", "")
            preview = (
                _format_chunk_preview(chunk_text) if chunk_text else "<empty text>"
            )
            logger.info("  %d. [%s] %s", index, chunk_id, preview)
    else:
        logger.info("No chunks returned.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the retrieval pipeline")
    parser.add_argument("query", help="Natural-language query to retrieve against")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum chunks to display (default: 5)",
    )
    args = parser.parse_args()
    if args.limit <= 0:
        parser.error("--limit must be a positive integer")
    asyncio.run(main(args.query, args.limit))
