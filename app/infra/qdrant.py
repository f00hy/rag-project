"""Vector database connection and initialization for Qdrant."""

from os import getenv

from qdrant_client import AsyncQdrantClient, models

from app.config import COLLECTION_NAME, DENSE_MODEL_NAME

vec_db_client = AsyncQdrantClient(
    url=(getenv("QDRANT_URL", ":memory:")),
    api_key=(getenv("QDRANT_API_KEY", None)),
    prefer_grpc=True,
    https=True,
    timeout=30,
)


async def init_vec_db() -> None:
    """Create the collection if it doesn't exist, with dense and sparse vector configs, scalar quantization, and payload indexes."""
    if not await vec_db_client.collection_exists(COLLECTION_NAME):
        await vec_db_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": models.VectorParams(
                    size=vec_db_client.get_embedding_size(DENSE_MODEL_NAME),
                    distance=models.Distance.COSINE,
                    datatype=models.Datatype.FLOAT16,
                    on_disk=True,
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(
                        datatype=models.Datatype.FLOAT16,
                    ),
                ),
            },
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    quantile=0.99,
                    always_ram=True,
                ),
            ),
            on_disk_payload=True,
        )

        await vec_db_client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="parent_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        await vec_db_client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="document_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
