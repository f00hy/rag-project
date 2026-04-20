"""Query API router."""

import logging

from fastapi import APIRouter

from app.api.schemas import (
    QueryCitation,
    QueryContextChunk,
    QueryRequest,
    QueryResponse,
)
from app.pipelines.generation import generate

router = APIRouter(prefix="/query", tags=["query"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    """Answer user queries with retrieval-grounded generation."""
    logger.info("Query request received: query=%s", request.query)
    run_error_msg = None
    answer = ""
    context_chunks: list[QueryContextChunk] = []
    citations: list[QueryCitation] = []

    try:
        result = await generate(request.query)
        answer = result.answer
        context_chunks = [
            QueryContextChunk(id=chunk.id, text=chunk.text)
            for chunk in result.context_chunks
        ]
        citations = [
            QueryCitation(
                parent_chunk_id=citation.parent_chunk_id,
                document_id=citation.document_id,
                source_url=citation.source_url,
            )
            for citation in result.citations
        ]
    except Exception as error:
        logger.exception("Query run failed")
        run_error_msg = str(error)
    finally:
        logger.debug(
            "Query request completed: has_error=%s context_chunks=%d citations=%d",
            bool(run_error_msg),
            len(context_chunks),
            len(citations),
        )

    return QueryResponse(
        query=request.query,
        answer=answer,
        context_chunks=context_chunks,
        citations=citations,
        run_error_msg=run_error_msg,
    )
