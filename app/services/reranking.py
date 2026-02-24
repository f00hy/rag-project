"""Rerank retrieved chunks using a cross-encoder model."""

from fastembed.rerank.cross_encoder import TextCrossEncoder

from app.config import CROSS_ENCODER_NAME, TOP_K_RERANK_CHUNKS
from app.models import ParentChunk

_cross_encoder = TextCrossEncoder(model_name=CROSS_ENCODER_NAME)


def rerank(query: str, parent_chunks: list[ParentChunk]) -> list[ParentChunk]:
    """Score each chunk against the query via cross-encoder and return the top-k by relevance.

    Args:
        query: User search query to rank against.
        parent_chunks: Candidate chunks to rerank.

    Returns:
        Top-k parent chunks sorted by descending relevance score.
    """
    texts = [chunk.text for chunk in parent_chunks]
    scores = list(_cross_encoder.rerank(query, texts, batch_size=16))
    ranking = sorted(zip(parent_chunks, scores), key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in ranking[:TOP_K_RERANK_CHUNKS]]
