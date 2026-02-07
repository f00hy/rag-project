"""Text embedding service using hybrid dense and sparse embeddings."""

from fastembed import TextEmbedding, SparseTextEmbedding
from qdrant_client.models import SparseVector
from app.models import Chunk, Embedding
from app.config import DENSE_MODEL_NAME, SPARSE_MODEL_NAME

dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)


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
            chunk_id=chunk.id,
            dense_embedding=dense_embedding.tolist(),
            sparse_embedding=SparseVector(
                indices=sparse_embedding.indices.tolist(),
                values=sparse_embedding.values.tolist(),
            ),
        )
        for chunk, dense_embedding, sparse_embedding in zip(
            chunks, dense_embeddings, sparse_embeddings
        )
    ]
