"""Tests for the vector search service."""

from uuid import uuid4

from qdrant_client import models

from app.config import COLLECTION_NAME
from app.models import Embedding
from app.services.searching import search
from tests.constants import DENSE_DIM


async def test_search_returns_parent_ids(patch_vec_db, vec_db):
    """Search returns UUIDs of parent chunks from matching points."""
    parent_id_1 = str(uuid4())
    parent_id_2 = str(uuid4())
    doc_id = str(uuid4())

    points = [
        models.PointStruct(
            id=str(uuid4()),
            vector={
                "dense": [0.9] + [0.0] * (DENSE_DIM - 1),
                "sparse": models.SparseVector(indices=[0, 1], values=[0.8, 0.5]),
            },
            payload={"parent_id": parent_id_1, "document_id": doc_id},
        ),
        models.PointStruct(
            id=str(uuid4()),
            vector={
                "dense": [0.8] + [0.0] * (DENSE_DIM - 1),
                "sparse": models.SparseVector(indices=[0, 2], values=[0.7, 0.4]),
            },
            payload={"parent_id": parent_id_2, "document_id": doc_id},
        ),
    ]
    await vec_db.upsert(collection_name=COLLECTION_NAME, points=points)

    query_embedding = Embedding(
        dense=[0.85] + [0.0] * (DENSE_DIM - 1),
        sparse=models.SparseVector(indices=[0, 1], values=[0.6, 0.3]),
    )
    result = await search(query_embedding)

    assert isinstance(result, list)
    assert len(result) > 0
    for uid in result:
        assert str(uid) in {parent_id_1, parent_id_2}


async def test_search_empty_collection_returns_empty(patch_vec_db):
    """Searching an empty collection returns an empty list."""
    query_embedding = Embedding(
        dense=[0.5] * DENSE_DIM,
        sparse=models.SparseVector(indices=[0], values=[1.0]),
    )
    result = await search(query_embedding)
    assert result == []
