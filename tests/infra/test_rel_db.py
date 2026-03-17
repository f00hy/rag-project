"""Smoke tests for the in-memory relational database session."""

from uuid import uuid4

from sqlmodel import select

from app.models import Document, ParentChunk


async def test_create_and_read_document(rel_db):
    """A persisted Document can be read back by primary key."""
    doc = Document(
        id=uuid4(),
        title="Test Document",
        content_key="test_key",
        content_hash="abc123",
        source_url="https://example.com",
    )
    async with rel_db() as session:
        session.add(doc)
        await session.commit()

    async with rel_db() as session:
        result = await session.get(Document, doc.id)
        assert result is not None
        assert result.title == "Test Document"
        assert result.content_key == "test_key"


async def test_create_document_with_parent_chunks(rel_db):
    """ParentChunks linked to a Document are queryable by document_id."""
    doc = Document(
        id=uuid4(),
        title="Doc",
        content_key="k",
        content_hash="h",
        source_url="https://example.com",
    )
    chunk = ParentChunk(id=uuid4(), text="some text", document=doc)
    doc.parent_chunks = [chunk]

    async with rel_db() as session:
        session.add(doc)
        await session.commit()

    async with rel_db() as session:
        result = await session.exec(
            select(ParentChunk).where(ParentChunk.document_id == doc.id)
        )
        chunks = result.all()
        assert len(chunks) == 1
        assert chunks[0].text == "some text"


async def test_document_without_chunks(rel_db):
    """A Document can be stored without any ParentChunks."""
    doc = Document(
        id=uuid4(),
        title="Solo",
        content_key="solo_k",
        content_hash="solo_h",
        source_url="https://example.com/solo",
    )
    async with rel_db() as session:
        session.add(doc)
        await session.commit()

    async with rel_db() as session:
        stored = await session.get(Document, doc.id)
        assert stored is not None
        assert stored.title == "Solo"
