"""Retrieval pipeline: query embedding, vector search, and reranking."""

import logging

from sqlmodel import col, select

from app.infra.postgres import rel_db_session
from app.models import ParentChunk
from app.services.embedding import embed_query
from app.services.reranking import rerank
from app.services.searching import search

logger = logging.getLogger(__name__)


async def retrieve(query: str) -> list[ParentChunk]:
    """Embed, search, fetch, and rerank parent chunks for a query.

    Args:
        query: Natural-language search query.

    Returns:
        Parent chunks ordered by relevance.
    """
    logger.info("Retrieval started for query: %s", query)
    embedding = await embed_query(query)
    parent_ids = await search(embedding)
    if not parent_ids:
        logger.warning("No results found for query: %s", query)
        return []
    async with rel_db_session() as session:
        result = await session.exec(
            select(ParentChunk).where(col(ParentChunk.id).in_(parent_ids))
        )
        parent_chunks = list(result.all())
    if len(parent_chunks) != len(parent_ids):
        logger.warning(
            "Fetched %d parent chunks for %d parent_id(s) — %d missing",
            len(parent_chunks),
            len(parent_ids),
            len(parent_ids) - len(parent_chunks),
        )
    else:
        logger.debug("Fetched %d parent chunks from database", len(parent_chunks))
    reranked_chunks = await rerank(query, parent_chunks)
    logger.debug("Retrieval complete — returning %d chunks", len(reranked_chunks))
    return reranked_chunks
