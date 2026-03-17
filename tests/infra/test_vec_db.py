"""Smoke tests for the in-memory vector database client."""

from uuid import uuid4

from qdrant_client import models

from app.config import COLLECTION_NAME
from tests.constants import DENSE_DIM


async def test_upsert_and_retrieve_points(vec_db):
    """Upserted points can be retrieved by ID with their payloads."""
    point_id = str(uuid4())
    dense_vec = [0.1] * DENSE_DIM
    sparse_vec = models.SparseVector(indices=[0, 5, 10], values=[0.5, 0.8, 0.3])

    await vec_db.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=point_id,
                vector={"dense": dense_vec, "sparse": sparse_vec},
                payload={"parent_id": "p1", "document_id": "d1"},
            )
        ],
    )

    results = await vec_db.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[point_id],
        with_payload=True,
    )
    assert len(results) == 1
    assert results[0].payload["parent_id"] == "p1"
    assert results[0].payload["document_id"] == "d1"


async def test_collection_exists(vec_db):
    """The fixture-created collection is reported as existing."""
    assert await vec_db.collection_exists(COLLECTION_NAME) is True


async def test_delete_points_by_filter(vec_db):
    """Points matching a filter are removed after deletion."""
    point_id = str(uuid4())
    await vec_db.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=point_id,
                vector={
                    "dense": [0.2] * DENSE_DIM,
                    "sparse": models.SparseVector(indices=[1], values=[0.4]),
                },
                payload={"parent_id": "px", "document_id": "dx"},
            )
        ],
    )

    await vec_db.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value="dx"),
                    )
                ]
            )
        ),
    )

    results = await vec_db.retrieve(
        collection_name=COLLECTION_NAME, ids=[point_id], with_payload=True
    )
    assert len(results) == 0
