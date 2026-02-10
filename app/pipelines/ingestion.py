"""Data ingestion pipeline: crawl result -> chunk -> embed -> store."""

from hashlib import sha256
from uuid import uuid4
from urllib.parse import urlparse
from asyncio import to_thread
from crawl4ai.models import CrawlResult
from qdrant_client.models import PointStruct
from app.config import BUCKET_NAME, COLLECTION_NAME
from app.models import Document, ParentChunk
from app.infra.cfr2 import obj_store_client
from app.infra.qdrant import vec_db_client
from app.infra.supabase import rel_db_session
from app.services.chunking import chunk
from app.services.embedding import embed


async def ingest(result: CrawlResult) -> None:
    """Process a crawl result by chunking, embedding, and persisting to all stores.

    Args:
        result: Crawl result containing the page URL, metadata, and markdown content.
    """
    # Extract content
    title = result.metadata.get("title") if result.metadata else result.url
    content = result.markdown.fit_markdown or ""
    if not content:
        return
    content_hash = sha256(content.encode("utf-8")).hexdigest()
    parsed_url = urlparse(result.url)
    content_key = f"{parsed_url.netloc}{parsed_url.path}".replace("/", "_")

    # Chunk content
    parents, children = await to_thread(chunk, content)

    # Embed child chunks
    embeddings = await to_thread(embed, children)

    # Initialize document object
    document = Document(
        title=title,
        content_key=content_key,
        source_url=result.url,
        content_hash=content_hash,
    )

    # Initialize parent chunk objects
    parent_chunks: list[ParentChunk] = []
    parent_id_map: dict[str, ParentChunk] = {}
    for parent in parents:
        parent_chunk = ParentChunk(
            text=parent.text,
            document=document,
        )
        parent_chunks.append(parent_chunk)
        parent_id_map[parent.id] = parent_chunk

    # Store content in object store
    async with obj_store_client() as client:
        await client.put_object(
            Bucket=BUCKET_NAME,
            Key=content_key,
            Body=content,
            ContentType="text/markdown",
        )

    # Store child chunks in vector database
    await vec_db_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=str(uuid4()),
                vector={
                    "dense": emb.dense_embedding,
                    "sparse": emb.sparse_embedding,
                },
                payload={
                    "parent_id": str(parent_id_map[child.parent_id].id),
                    "document_id": str(document.id),
                },
            )
            for child, emb in zip(children, embeddings)
        ],
    )

    # Store document and parent chunks in relational database
    # Placed after Qdrant upsertions to avoid object refreshing
    # https://sqlmodel.tiangolo.com/tutorial/automatic-id-none-refresh/
    async with rel_db_session() as session:
        session.add(document)
        session.add_all(parent_chunks)
        await session.commit()
