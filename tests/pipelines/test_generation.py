"""Tests for the generation pipeline."""

import importlib
import sys
import types
from unittest.mock import AsyncMock
from uuid import uuid4

from app.models import Document, ParentChunk


def _import_generation_module(monkeypatch):
    """Import generation module with a stubbed retrieval dependency."""

    async def _retrieve_stub(_query: str):
        return []

    retrieval_stub = types.ModuleType("app.pipelines.retrieval")
    setattr(retrieval_stub, "retrieve", _retrieve_stub)
    monkeypatch.setitem(sys.modules, "app.pipelines.retrieval", retrieval_stub)

    module = importlib.import_module("app.pipelines.generation")
    return importlib.reload(module)


async def test_generate_returns_message_on_empty_retrieval(monkeypatch):
    """generate() returns a no-context answer when retrieval is empty."""
    generation = _import_generation_module(monkeypatch)
    monkeypatch.setattr(
        "app.pipelines.generation.retrieve",
        AsyncMock(return_value=[]),
    )

    result = await generation.generate("What is this?")

    assert "I could not find relevant context" in result.answer
    assert result.context_chunks == []
    assert result.citations == []


async def test_generate_maps_context_and_citations(monkeypatch):
    """generate() maps retrieved chunks and returns collaborator outputs."""
    generation = _import_generation_module(monkeypatch)
    doc_id = uuid4()
    chunk_one = ParentChunk(id=uuid4(), text="Chunk one", document_id=doc_id)
    chunk_two = ParentChunk(id=uuid4(), text="Chunk two", document_id=doc_id)
    citations = [
        generation.GeneratedCitation(
            parent_chunk_id=chunk_one.id,
            document_id=doc_id,
            source_url="https://example.com/one",
        ),
        generation.GeneratedCitation(
            parent_chunk_id=chunk_two.id,
            document_id=doc_id,
            source_url="https://example.com/two",
        ),
    ]

    monkeypatch.setattr(
        "app.pipelines.generation.retrieve",
        AsyncMock(return_value=[chunk_one, chunk_two]),
    )
    monkeypatch.setattr(
        "app.pipelines.generation._build_citations",
        AsyncMock(return_value=citations),
    )
    monkeypatch.setattr(
        "app.pipelines.generation._generate_answer",
        AsyncMock(return_value="Final answer"),
    )

    result = await generation.generate("test query")

    assert result.answer == "Final answer"
    assert [chunk.id for chunk in result.context_chunks] == [chunk_one.id, chunk_two.id]
    assert [chunk.text for chunk in result.context_chunks] == ["Chunk one", "Chunk two"]
    assert result.citations == citations


async def test_build_citations_returns_metadata(monkeypatch, rel_db):
    """_build_citations() includes document metadata when rows exist."""
    generation = _import_generation_module(monkeypatch)
    monkeypatch.setattr("app.pipelines.generation.rel_db_session", rel_db)

    doc = Document(
        id=uuid4(),
        title="Doc",
        content_key="doc-key",
        content_hash="hash",
        source_url="https://example.com/source",
    )
    parent_chunk = ParentChunk(id=uuid4(), text="Text", document_id=doc.id)

    async with rel_db() as session:
        session.add(doc)
        session.add(parent_chunk)
        await session.commit()

    citations = await generation._build_citations([parent_chunk])

    assert len(citations) == 1
    assert citations[0].parent_chunk_id == parent_chunk.id
    assert citations[0].document_id == doc.id
    assert str(citations[0].source_url) == "https://example.com/source"


async def test_build_citations_returns_fallback_for_missing_row(monkeypatch, rel_db):
    """_build_citations() falls back when a chunk has no DB row."""
    generation = _import_generation_module(monkeypatch)
    monkeypatch.setattr("app.pipelines.generation.rel_db_session", rel_db)

    doc = Document(
        id=uuid4(),
        title="Doc",
        content_key="doc-key",
        content_hash="hash",
        source_url="https://example.com/source",
    )
    existing_chunk = ParentChunk(id=uuid4(), text="Existing", document_id=doc.id)
    missing_chunk = ParentChunk(id=uuid4(), text="Missing", document_id=uuid4())

    async with rel_db() as session:
        session.add(doc)
        session.add(existing_chunk)
        await session.commit()

    citations = await generation._build_citations([existing_chunk, missing_chunk])

    assert len(citations) == 2
    assert citations[0].parent_chunk_id == existing_chunk.id
    assert citations[0].document_id == doc.id
    assert citations[1].parent_chunk_id == missing_chunk.id
    assert citations[1].document_id is None
    assert citations[1].source_url is None


async def test_generate_answer_uses_fallback_without_api_key(monkeypatch):
    """_generate_answer() uses fallback when API key is missing."""
    generation = _import_generation_module(monkeypatch)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    context = [generation.GeneratedContextChunk(id=uuid4(), text="Important context")]

    answer = await generation._generate_answer("question", context)

    assert answer.startswith("Unable to call the language model right now.")
    assert "Important context" in answer


async def test_generate_answer_uses_fallback_on_llm_error(monkeypatch):
    """_generate_answer() falls back when the LLM call fails."""
    generation = _import_generation_module(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.pipelines.generation.to_thread",
        AsyncMock(side_effect=RuntimeError("llm down")),
    )
    context = [generation.GeneratedContextChunk(id=uuid4(), text="Primary context")]

    answer = await generation._generate_answer("question", context)

    assert answer.startswith("Unable to call the language model right now.")
    assert "Primary context" in answer


def test_build_prompt_includes_question_and_numbered_context(monkeypatch):
    """_build_prompt() includes question and numbered context chunks."""
    generation = _import_generation_module(monkeypatch)
    chunks = [
        generation.GeneratedContextChunk(id=uuid4(), text="First chunk"),
        generation.GeneratedContextChunk(id=uuid4(), text="Second chunk"),
    ]

    prompt = generation._build_prompt("What happened?", chunks)

    assert "Question:\nWhat happened?" in prompt
    assert "[1] First chunk" in prompt
    assert "[2] Second chunk" in prompt
    assert prompt.endswith("Answer:")


def test_fallback_answer_with_context_preview(monkeypatch):
    """_fallback_answer() includes trimmed preview when context exists."""
    generation = _import_generation_module(monkeypatch)
    chunks = [
        generation.GeneratedContextChunk(id=uuid4(), text="  useful   context  text  ")
    ]

    answer = generation._fallback_answer(chunks)

    assert answer.startswith("Unable to call the language model right now.")
    assert "useful context text" in answer


def test_fallback_answer_without_context(monkeypatch):
    """_fallback_answer() returns generic message when context is empty."""
    generation = _import_generation_module(monkeypatch)
    answer = generation._fallback_answer([])
    assert answer == "Unable to generate an answer right now."
