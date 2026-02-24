"""Text embedding service using hybrid dense and sparse embeddings."""

from asyncio import to_thread

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client.models import SparseVector

from app.config import DENSE_MODEL_NAME, SPARSE_MODEL_NAME
from app.models import Chunk, Embedding

_dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
_sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)


def _embed_chunks_sync(chunks: list[Chunk]) -> list[Embedding]:
    texts = [chunk.text for chunk in chunks]
    dense_embeddings = list(_dense_model.embed(texts, batch_size=16))
    sparse_embeddings = list(_sparse_model.embed(texts, batch_size=16))
    return [
        Embedding(
            chunk_id=chunk.id,
            dense=dense_embedding.tolist(),
            sparse=SparseVector(
                indices=sparse_embedding.indices.tolist(),
                values=sparse_embedding.values.tolist(),
            ),
        )
        for chunk, dense_embedding, sparse_embedding in zip(
            chunks, dense_embeddings, sparse_embeddings
        )
    ]


async def embed_chunks(chunks: list[Chunk]) -> list[Embedding]:
    """Generate dense and sparse embeddings for text chunks.

    Args:
        chunks: List of text chunks to embed.

    Returns:
        List of embeddings with both dense and sparse vectors.
    """
    return await to_thread(_embed_chunks_sync, chunks)


def _embed_query_sync(query: str) -> Embedding:
    [dense_embedding] = _dense_model.query_embed(query)
    [sparse_embedding] = _sparse_model.query_embed(query)
    return Embedding(
        dense=dense_embedding.tolist(),
        sparse=SparseVector(
            indices=sparse_embedding.indices.tolist(),
            values=sparse_embedding.values.tolist(),
        ),
    )


async def embed_query(query: str) -> Embedding:
    """Generate dense and sparse embeddings for a query string.

    Args:
        query: The query to embed.

    Returns:
        Embedding with both dense and sparse vectors.
    """
    return await to_thread(_embed_query_sync, query)
