"""Vector search service using Qdrant hybrid retrieval with RRF fusion."""

from qdrant_client import models

from app.config import COLLECTION_NAME, OVERSAMPLING_FACTOR, TOP_K_CHUNKS
from app.infra.qdrant import vec_db_client
from app.models import Embedding


async def search(embedding: Embedding) -> tuple[list[str], list[str]]:
    """Run a hybrid search combining dense and sparse vectors, grouped by parent chunk ID.

    Args:
        embedding: Dense and sparse vectors for the query.

    Returns:
        Tuple of (parent_ids, document_ids) for the top matching chunks.
    """
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
                limit=10,
            ),
            models.Prefetch(
                query=embedding.sparse,
                using="sparse",
                limit=10,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        group_by="parent_id",
        group_size=1,
        limit=TOP_K_CHUNKS,
    )

    parent_ids, document_ids = [], []
    for hit in (group.hits[0] for group in result.groups):
        if hit.payload is None:
            continue
        parent_ids.append(hit.payload["parent_id"])
        document_ids.append(hit.payload["document_id"])

    return parent_ids, document_ids
