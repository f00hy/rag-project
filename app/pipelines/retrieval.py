"""Retrieval pipeline: query embedding, vector search, and reranking."""

from sqlmodel import col, select

from app.infra.supabase import rel_db_session
from app.models import ParentChunk
from app.services.embedding import embed_query
from app.services.reranking import rerank
from app.services.searching import search


async def retrieve(query: str) -> list[ParentChunk]:
    """Embed, search, fetch, and rerank parent chunks for a query.

    Args:
        query: Natural-language search query.

    Returns:
        Parent chunks ordered by relevance.
    """
    embedding = await embed_query(query)
    parent_ids = await search(embedding)
    if not parent_ids:
        return []
    async with rel_db_session() as session:
        result = await session.exec(
            select(ParentChunk).where(col(ParentChunk.id).in_(parent_ids))
        )
        parent_chunks = list(result.all())
    return await rerank(query, parent_chunks)
