"""Tests for the indexing services (R2, Qdrant, Supabase)."""

from uuid import uuid4

from qdrant_client import models
from sqlmodel import select

from app.config import BUCKET_NAME, COLLECTION_NAME
from app.models import Document, ParentChunk
from app.services.indexing import index_obj_store, index_rel_db, index_vec_db
from tests.constants import DENSE_DIM


async def test_index_obj_store(patch_obj_store, obj_store):
    """Content is stored in R2 with expected key and content type."""
    await index_obj_store("test_key", "# Markdown content")
    obj = await obj_store.get_object(Bucket=BUCKET_NAME, Key="test_key")
    assert obj["Body"] == "# Markdown content"
    assert obj["ContentType"] == "text/markdown"


async def test_index_vec_db_upsert(patch_vec_db, vec_db):
    """Points are upserted into Qdrant."""
    point_id = str(uuid4())
    points = [
        models.PointStruct(
            id=point_id,
            vector={
                "dense": [0.1] * DENSE_DIM,
                "sparse": models.SparseVector(indices=[1, 2], values=[0.5, 0.3]),
            },
            payload={"parent_id": "p1", "document_id": "d1"},
        )
    ]
    await index_vec_db(points)

    result = await vec_db.retrieve(
        collection_name=COLLECTION_NAME, ids=[point_id], with_payload=True
    )
    assert len(result) == 1
    assert result[0].payload["parent_id"] == "p1"


async def test_index_vec_db_deletes_stale_vectors(patch_vec_db, vec_db):
    """Stale vectors are removed before upserting new ones."""
    doc_id = uuid4()
    old_point_id = str(uuid4())
    new_point_id = str(uuid4())

    await vec_db.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=old_point_id,
                vector={
                    "dense": [0.2] * DENSE_DIM,
                    "sparse": models.SparseVector(indices=[3], values=[0.7]),
                },
                payload={"parent_id": "old_p", "document_id": str(doc_id)},
            )
        ],
    )

    new_points = [
        models.PointStruct(
            id=new_point_id,
            vector={
                "dense": [0.3] * DENSE_DIM,
                "sparse": models.SparseVector(indices=[4], values=[0.6]),
            },
            payload={"parent_id": "new_p", "document_id": str(doc_id)},
        )
    ]
    await index_vec_db(new_points, stale_document_id=doc_id)

    old_result = await vec_db.retrieve(
        collection_name=COLLECTION_NAME, ids=[old_point_id], with_payload=True
    )
    new_result = await vec_db.retrieve(
        collection_name=COLLECTION_NAME, ids=[new_point_id], with_payload=True
    )
    assert len(old_result) == 0
    assert len(new_result) == 1
    assert new_result[0].payload["parent_id"] == "new_p"


async def test_index_rel_db_new_document(patch_rel_db, rel_db):
    """A new document with parent chunks is persisted."""
    doc = Document(
        id=uuid4(),
        title="Test",
        content_key="k",
        content_hash="h",
        source_url="https://example.com",
    )
    doc.parent_chunks = [ParentChunk(id=uuid4(), text="chunk text", document=doc)]

    await index_rel_db(doc, existing=False)

    async with rel_db() as session:
        stored = await session.get(Document, doc.id)
        assert stored is not None
        assert stored.title == "Test"
        result = await session.exec(
            select(ParentChunk).where(ParentChunk.document_id == doc.id)
        )
        assert len(result.all()) == 1


async def test_index_rel_db_existing_replaces_chunks(patch_rel_db, rel_db):
    """Updating an existing document replaces stale parent chunks."""
    doc_id = uuid4()
    doc = Document(
        id=doc_id,
        title="Original",
        content_key="k",
        content_hash="h1",
        source_url="https://example.com",
    )
    doc.parent_chunks = [ParentChunk(id=uuid4(), text="old chunk", document=doc)]

    async with rel_db() as session:
        session.add(doc)
        await session.commit()

    updated = Document(
        id=doc_id,
        title="Updated",
        content_key="k",
        content_hash="h2",
        source_url="https://example.com",
    )
    updated.parent_chunks = [
        ParentChunk(id=uuid4(), text="new chunk", document=updated)
    ]
    await index_rel_db(updated, existing=True)

    async with rel_db() as session:
        stored = await session.get(Document, doc_id)
        assert stored.title == "Updated"
        result = await session.exec(
            select(ParentChunk).where(ParentChunk.document_id == doc_id)
        )
        chunks = result.all()
        assert len(chunks) == 1
        assert chunks[0].text == "new chunk"
