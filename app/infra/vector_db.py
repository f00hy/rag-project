from os import getenv
from qdrant_client import QdrantClient, models
from app.config import (
    DENSE_MODEL_NAME,
    QDRANT_COLLECTION_NAME,
    QDRANT_PAYLOAD_INDEX_FIELD_NAME,
)

client = QdrantClient(
    url=(getenv("QDRANT_URL") or ":memory:"),
    api_key=(getenv("QDRANT_API_KEY") or None),
    prefer_grpc=True,
    https=True,
    timeout=30,
)

if not client.collection_exists(QDRANT_COLLECTION_NAME):
    client.create_collection(
        collection_name=QDRANT_COLLECTION_NAME,
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

    client.create_payload_index(
        collection_name=QDRANT_COLLECTION_NAME,
        field_name=QDRANT_PAYLOAD_INDEX_FIELD_NAME,
        field_schema=models.PayloadSchemaType.KEYWORD,
    )


def get_vector_db_client() -> QdrantClient:
    return client
