"""Data ingestion pipeline: crawl result -> chunk -> embed -> index."""

import logging
from hashlib import sha256
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5

from crawl4ai.models import CrawlResult
from qdrant_client import models

from app.infra.supabase import rel_db_session
from app.models import Document, ParentChunk
from app.services.chunking import chunk
from app.services.embedding import embed_chunks
from app.services.indexing import index_obj_store, index_rel_db, index_vec_db

logger = logging.getLogger(__name__)


async def ingest(result: CrawlResult) -> None:
    """Chunk, embed, and index a crawl result, skipping unchanged content.

    Stale vectors and parent chunks are removed before upserting updated data.

    Args:
        result: Crawl result containing the page URL, metadata, and markdown content.
    """
    logger.info("Ingesting crawl result for %s", result.url)

    # Extract content
    title = result.metadata.get("title") if result.metadata else result.url
    content = result.markdown.fit_markdown or ""
    if not content:
        logger.warning("Empty content for %s — skipping", result.url)
        return
    content_hash = sha256(content.encode("utf-8")).hexdigest()
    parsed_url = urlparse(result.url)
    content_key = f"{parsed_url.netloc}{parsed_url.path}".replace("/", "_")

    # Initialize document object
    document = Document(
        id=uuid5(NAMESPACE_URL, content_key),
        title=title,
        content_key=content_key,
        source_url=result.url,
        content_hash=content_hash,
    )

    # Check if document already exists and content is unchanged
    logger.info("Checking for existing document: %s", document.id)
    async with rel_db_session() as session:
        existing = await session.get(Document, document.id)
        if existing and existing.content_hash == content_hash:
            logger.debug("Content unchanged for %s — skipping", result.url)
            return

    # Chunk content
    parents, children = await chunk(content)

    # Embed child chunks
    embeddings = await embed_chunks(children)

    # Initialize parent chunk objects
    parent_chunks: list[ParentChunk] = []
    parent_id_map: dict[str, ParentChunk] = {}
    for parent in parents:
        parent_chunk = ParentChunk(
            id=uuid5(NAMESPACE_URL, f"{content_key}:{parent.id}"),
            text=parent.text,
            document=document,
        )
        parent_chunks.append(parent_chunk)
        parent_id_map[parent.id] = parent_chunk

    # Build vector points
    points = [
        models.PointStruct(
            id=str(uuid5(NAMESPACE_URL, f"{content_key}:{child.id}")),
            vector={
                "dense": embedding.dense,
                "sparse": embedding.sparse,
            },
            payload={
                "parent_id": str(parent_id_map[child.parent_id].id),
                "document_id": str(document.id),
            },
        )
        for child, embedding in zip(children, embeddings)
    ]

    # Index across stores
    await index_obj_store(content_key, content)
    await index_vec_db(points, stale_document_id=document.id if existing else None)
    await index_rel_db(document, existing=bool(existing))

    logger.debug("Ingestion complete for %s", result.url)
