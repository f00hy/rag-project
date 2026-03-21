"""Shared fixtures for the test suite."""

import pytest
from qdrant_client import AsyncQdrantClient, models
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import COLLECTION_NAME
from tests.constants import DENSE_DIM
from tests.stubs.obj_store_stub import ObjStoreStubClient, make_obj_store_stub


@pytest.fixture
async def vec_db():
    """Fresh in-memory Qdrant client with production-like schema."""
    client = AsyncQdrantClient(location=":memory:")
    await client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": models.VectorParams(
                size=DENSE_DIM,
                distance=models.Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "sparse": models.SparseVectorParams(),
        },
    )
    await client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="parent_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    await client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="document_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    yield client
    await client.close()


@pytest.fixture
async def rel_db():
    """Fresh in-memory SQLite session factory with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture
def obj_store():
    """Fresh in-memory object store stub client."""
    return ObjStoreStubClient()


@pytest.fixture
def patch_vec_db(monkeypatch, vec_db):
    """Replace ``vec_db_client`` in all modules that import it."""
    monkeypatch.setattr("app.infra.qdrant.vec_db_client", vec_db)
    monkeypatch.setattr("app.services.indexing.vec_db_client", vec_db)
    monkeypatch.setattr("app.services.searching.vec_db_client", vec_db)


@pytest.fixture
def patch_rel_db(monkeypatch, rel_db):
    """Replace ``rel_db_session`` in all modules that import it."""
    monkeypatch.setattr("app.infra.postgres.rel_db_session", rel_db)
    monkeypatch.setattr("app.services.indexing.rel_db_session", rel_db)
    monkeypatch.setattr("app.pipelines.ingestion.rel_db_session", rel_db)
    monkeypatch.setattr("app.pipelines.retrieval.rel_db_session", rel_db)


@pytest.fixture
def patch_obj_store(monkeypatch, obj_store):
    """Replace ``obj_store_client`` in all modules that import it."""
    factory = make_obj_store_stub(obj_store)
    monkeypatch.setattr("app.infra.cfr2.obj_store_client", factory)
    monkeypatch.setattr("app.services.indexing.obj_store_client", factory)
