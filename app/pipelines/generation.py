"""Generation pipeline: retrieve context and synthesize an answer."""

import logging
from asyncio import to_thread
from os import getenv
from uuid import UUID

from pydantic import BaseModel, HttpUrl
from sqlmodel import col, select

from app.infra.postgres import rel_db_session
from app.models import Document, ParentChunk
from app.pipelines.retrieval import retrieve

logger = logging.getLogger(__name__)


class GeneratedContextChunk(BaseModel):
    """Context chunk returned by the generation pipeline."""

    id: UUID
    text: str


class GeneratedCitation(BaseModel):
    """Citation metadata derived from retrieved parent chunks."""

    parent_chunk_id: UUID
    document_id: UUID | None = None
    source_url: HttpUrl | None = None


class GenerationResult(BaseModel):
    """Generated answer plus supporting context and citations."""

    answer: str
    context_chunks: list[GeneratedContextChunk] = []
    citations: list[GeneratedCitation] = []


async def generate(query: str) -> GenerationResult:
    """Generate an answer for a query using retrieved parent chunks."""
    logger.info("Generation started for query: %s", query)
    parent_chunks = await retrieve(query)
    if not parent_chunks:
        logger.warning("Generation skipped due to empty retrieval result")
        return GenerationResult(
            answer=(
                "I could not find relevant context to answer this question yet. "
                "Try refining your query or indexing more pages."
            )
        )

    context_chunks = [
        GeneratedContextChunk(id=parent_chunk.id, text=parent_chunk.text)
        for parent_chunk in parent_chunks
    ]
    citations = await _build_citations(parent_chunks)
    answer = await _generate_answer(query, context_chunks)

    logger.debug(
        "Generation complete: context_chunks=%d citations=%d",
        len(context_chunks),
        len(citations),
    )
    return GenerationResult(
        answer=answer,
        context_chunks=context_chunks,
        citations=citations,
    )


async def _build_citations(parent_chunks: list[ParentChunk]) -> list[GeneratedCitation]:
    """Build citation metadata for retrieved parent chunks."""
    parent_ids = [parent_chunk.id for parent_chunk in parent_chunks]
    async with rel_db_session() as session:
        result = await session.exec(
            select(ParentChunk, Document)
            .join(Document, col(Document.id) == col(ParentChunk.document_id))
            .where(col(ParentChunk.id).in_(parent_ids))
        )
        rows = list(result.all())

    citation_by_chunk_id = {
        parent_chunk.id: GeneratedCitation(
            parent_chunk_id=parent_chunk.id,
            document_id=parent_chunk.document_id,
            source_url=document.source_url,
        )
        for parent_chunk, document in rows
    }
    return [
        citation_by_chunk_id.get(
            parent_id, GeneratedCitation(parent_chunk_id=parent_id)
        )
        for parent_id in parent_ids
    ]


async def _generate_answer(
    query: str, context_chunks: list[GeneratedContextChunk]
) -> str:
    """Generate answer text from the query and retrieved context."""
    api_key = getenv("GEMINI_API_KEY", "").strip()
    model_name = getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set, using fallback answer synthesis")
        return _fallback_answer(context_chunks)

    prompt = _build_prompt(query, context_chunks)
    try:
        return await to_thread(_generate_answer_sync, api_key, model_name, prompt)
    except Exception:
        logger.exception("LLM generation failed, returning fallback answer")
        return _fallback_answer(context_chunks)


def _generate_answer_sync(api_key: str, model_name: str, prompt: str) -> str:
    """Run a blocking Gemini call and return plain text."""
    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model_name, contents=prompt)
    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Gemini response did not include text")
    return text.strip()


def _build_prompt(query: str, context_chunks: list[GeneratedContextChunk]) -> str:
    """Build a compact grounded-answer prompt."""
    numbered_context = "\n\n".join(
        f"[{index}] {chunk.text}" for index, chunk in enumerate(context_chunks, start=1)
    )
    return (
        "You are a grounded assistant. Use only the provided context to answer.\n"
        "If the context is insufficient, say so briefly.\n\n"
        f"Question:\n{query}\n\n"
        f"Context:\n{numbered_context}\n\n"
        "Answer:"
    )


def _fallback_answer(context_chunks: list[GeneratedContextChunk]) -> str:
    """Build a deterministic fallback answer when LLM is unavailable."""
    first_chunk = context_chunks[0].text if context_chunks else ""
    preview = " ".join(first_chunk.split())[:300]
    if preview:
        return (
            "Unable to call the language model right now. "
            f"Most relevant retrieved context: {preview}"
        )
    return "Unable to generate an answer right now."
