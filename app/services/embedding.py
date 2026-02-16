"""Text embedding service using hybrid dense and sparse embeddings."""

from fastembed import TextEmbedding, SparseTextEmbedding
from qdrant_client.models import SparseVector
from app.models import Chunk, Embedding
from app.config import DENSE_MODEL_NAME, SPARSE_MODEL_NAME

_dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
_sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)


def embed_chunks(chunks: list[Chunk]) -> list[Embedding]:
    """Generate dense and sparse embeddings for text chunks.

    Args:
        chunks: List of text chunks to embed.

    Returns:
        List of embeddings with both dense and sparse vectors.
    """
    texts = [chunk.text for chunk in chunks]
    dense_embeddings = list(_dense_model.embed(texts, batch_size=16))
    sparse_embeddings = list(_sparse_model.embed(texts, batch_size=16))
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


def embed_text(text: str) -> Embedding:
    """Generate dense and sparse embeddings for a text string.

    Args:
        text: The text to embed.

    Returns:
        Embedding with both dense and sparse vectors.
    """
    [dense_embedding] = _dense_model.embed(text)
    [sparse_embedding] = _sparse_model.embed(text)
    return Embedding(
        dense_embedding=dense_embedding.tolist(),
        sparse_embedding=SparseVector(
            indices=sparse_embedding.indices.tolist(),
            values=sparse_embedding.values.tolist(),
        ),
    )
