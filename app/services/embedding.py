"""Text embedding service using hybrid dense and sparse embeddings."""

from fastembed import TextEmbedding, SparseTextEmbedding
from app.models import Chunk, Embedding

dense_model = TextEmbedding(model_name="jinaai/jina-embeddings-v3")
sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")


def embed(chunks: list[Chunk]) -> list[Embedding]:
    """Generate dense and sparse embeddings for text chunks.

    Args:
        chunks: List of text chunks to embed.

    Returns:
        List of embeddings with both dense and sparse vectors.
    """
    texts = [chunk.text for chunk in chunks]
    dense_embeddings = list(dense_model.embed(texts))
    sparse_embeddings = list(sparse_model.embed(texts))
    return [
        Embedding(
            chunk_id=chunk.chunk_id,
            dense_embedding=dense_embedding,
            sparse_embedding=sparse_embedding,
        )
        for chunk, dense_embedding, sparse_embedding in zip(
            chunks, dense_embeddings, sparse_embeddings
        )
    ]
