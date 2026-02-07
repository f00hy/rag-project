from os import getenv
from qdrant_client import AsyncQdrantClient, models
from app.config import (
    DENSE_MODEL_NAME,
    COLLECTION_NAME,
)

client = AsyncQdrantClient(
    url=(getenv("QDRANT_URL", ":memory:")),
    api_key=(getenv("QDRANT_API_KEY", None)),
    prefer_grpc=True,
    https=True,
    timeout=30,
)


async def init_vector_db() -> None:
    if not await client.collection_exists(COLLECTION_NAME):
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": models.VectorParams(
                    size=client.get_embedding_size(DENSE_MODEL_NAME),
                    distance=models.Distance.COSINE,
                    datatype=models.Datatype.FLOAT16,
                    on_disk=True,
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(
                        datatype=models.Datatype.FLOAT16,
                    ),
                )
            },
            on_disk_payload=True,
        )
