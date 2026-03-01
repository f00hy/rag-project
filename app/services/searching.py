"""Vector search service using Qdrant hybrid retrieval with RRF fusion."""

import logging
from uuid import UUID

from qdrant_client import models

from app.config import (
    COLLECTION_NAME,
    OVERSAMPLING_FACTOR,
    TOP_K_PREFETCH_CHUNKS,
    TOP_K_SEARCH_CHUNKS,
)
from app.infra.qdrant import vec_db_client
from app.models import Embedding

logger = logging.getLogger(__name__)


async def search(embedding: Embedding) -> list[UUID]:
    """Run a hybrid search combining dense and sparse vectors, grouped by parent chunk ID.

    Args:
        embedding: Dense and sparse vectors for the query.

    Returns:
        List of parent chunk UUIDs for the top matching chunks.
    """
    logger.info("Running hybrid search (top_k=%d)", TOP_K_SEARCH_CHUNKS)
    result = await vec_db_client.query_points_groups(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(
                query=embedding.dense,
                params=models.SearchParams(
                    quantization=models.QuantizationSearchParams(
                        rescore=True,
                        oversampling=OVERSAMPLING_FACTOR,
                    ),
                ),
                using="dense",
                limit=TOP_K_PREFETCH_CHUNKS,
            ),
            models.Prefetch(
                query=embedding.sparse,
                using="sparse",
                limit=TOP_K_PREFETCH_CHUNKS,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        group_by="parent_id",
        group_size=1,
        limit=TOP_K_SEARCH_CHUNKS,
    )

    parent_ids = [
        UUID(hit.payload["parent_id"])
        for hit in (group.hits[0] for group in result.groups)
        if hit.payload is not None
    ]

    if not parent_ids:
        logger.warning("Search returned no results")
    else:
        logger.debug("Search returned %d parent chunk(s)", len(parent_ids))

    return parent_ids
