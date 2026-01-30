from os import getenv
from qdrant_client import QdrantClient, models
from app.config import DENSE_MODEL_NAME, QDRANT_COLLECTION_NAME

client = QdrantClient(getenv("QDRANT_URL") or ":memory:")

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
                    on_disk=True,
                ),
            )
        },
        hnsw_config=models.HnswConfigDiff(on_disk=True),
        on_disk_payload=True,
    )
