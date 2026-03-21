"""Indexing services for persisting data to object store, vector DB, and relational DB."""

import logging
from uuid import UUID

from qdrant_client import models
from sqlmodel import col, delete
from tenacity import RetryCallState, retry, stop_after_attempt, wait_exponential

from app.config import BUCKET_NAME, COLLECTION_NAME
from app.infra.cfr2 import obj_store_client
from app.infra.postgres import rel_db_session
from app.infra.qdrant import vec_db_client
from app.models import Document, ParentChunk

logger = logging.getLogger(__name__)


def _log_failure(retry_state: RetryCallState) -> None:
    """Logs an error when all retry attempts are exhausted.

    Args:
        retry_state: Tenacity state containing attempt info and the exception.
    """
    logger.error(
        "%s failed after %d attempts",
        retry_state.fn.__name__ if retry_state.fn else "unknown",
        retry_state.attempt_number,
        exc_info=retry_state.outcome.exception() if retry_state.outcome else None,
    )


_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, max=10),
    retry_error_callback=_log_failure,
)


@_retry
async def index_obj_store(content_key: str, content: str) -> None:
    """Stores markdown content in R2.

    Args:
        content_key: Object storage key for the content.
        content: Markdown string to store.
    """
    logger.info(
        "Storing content in R2: key=%s, size=%d bytes", content_key, len(content)
    )
    async with obj_store_client() as client:
        await client.put_object(
            Bucket=BUCKET_NAME,
            Key=content_key,
            Body=content,
            ContentType="text/markdown",
        )
    logger.debug("R2 put_object completed for key=%s", content_key)


@_retry
async def index_vec_db(
    points: list[models.PointStruct],
    stale_document_id: UUID | None = None,
) -> None:
    """Upserts child-chunk embeddings into Qdrant.

    Deletes stale vectors for the given document before upserting when
    `stale_document_id` is provided.

    Args:
        points: Qdrant point structs to upsert.
        stale_document_id: Document whose old vectors should be removed first.
    """
    logger.info(
        "Storing %d point(s) into vector DB (stale_document_id=%s)",
        len(points),
        stale_document_id,
    )
    if stale_document_id:
        await vec_db_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(stale_document_id)),
                        ),
                    ],
                ),
            ),
        )
        logger.debug("Deleted stale vectors for document_id=%s", stale_document_id)
    await vec_db_client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.debug("Vector DB upsert completed for %d points", len(points))


@_retry
async def index_rel_db(
    document: Document,
    existing: bool = False,
) -> None:
    """Persists a document and its parent chunks in PostgreSQL.

    When `existing` is True, stale parent chunks are deleted and the
    document is merged instead of inserted.

    Args:
        document: Document model instance (with nested parent chunks).
        existing: Whether this is an update to an existing document.
    """
    num_chunks = len(document.parent_chunks) if document.parent_chunks else 0
    logger.info(
        "Storing document to relational DB: id=%s, existing=%s, parent_chunks=%d",
        document.id,
        existing,
        num_chunks,
    )
    async with rel_db_session() as session:
        if existing:
            await session.exec(
                delete(ParentChunk).where(col(ParentChunk.document_id) == document.id)
            )
            await session.merge(document)
        else:
            session.add(document)
        await session.commit()
    logger.debug("Relational DB commit completed for document_id=%s", document.id)
