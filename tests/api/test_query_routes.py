"""Tests for the query API endpoint."""

import importlib
import sys
import types
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


def _build_test_app_with_generate(monkeypatch, generate_mock):
    """Create a FastAPI app with query router and stubbed generation dependency."""
    generation_stub = types.ModuleType("app.pipelines.generation")
    setattr(generation_stub, "generate", generate_mock)
    monkeypatch.setitem(sys.modules, "app.pipelines.generation", generation_stub)

    query_module = importlib.import_module("app.api.routes.query")
    query_module = importlib.reload(query_module)
    app = FastAPI()
    app.include_router(query_module.router)
    return app


async def test_query_endpoint_success(monkeypatch):
    """Successful query returns mapped answer, context, and citations."""
    chunk_one_id = uuid4()
    chunk_two_id = uuid4()
    citation_one_id = uuid4()
    citation_two_id = uuid4()
    result = types.SimpleNamespace(
        answer="Generated answer",
        context_chunks=[
            types.SimpleNamespace(id=chunk_one_id, text="Context one"),
            types.SimpleNamespace(id=chunk_two_id, text="Context two"),
        ],
        citations=[
            types.SimpleNamespace(
                parent_chunk_id=citation_one_id,
                document_id=uuid4(),
                source_url="https://example.com/doc-1",
            ),
            types.SimpleNamespace(
                parent_chunk_id=citation_two_id,
                document_id=uuid4(),
                source_url="https://example.com/doc-2",
            ),
        ],
    )
    app = _build_test_app_with_generate(
        monkeypatch,
        AsyncMock(return_value=result),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query/", json={"query": "What is RAG?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "What is RAG?"
    assert data["answer"] == "Generated answer"
    assert len(data["context_chunks"]) == 2
    assert data["context_chunks"][0]["text"] == "Context one"
    assert len(data["citations"]) == 2
    assert data["citations"][0]["source_url"] == "https://example.com/doc-1"
    assert data["run_error_msg"] is None


async def test_query_endpoint_captures_exception(monkeypatch):
    """Top-level exceptions are captured in run_error_msg."""
    app = _build_test_app_with_generate(
        monkeypatch,
        AsyncMock(side_effect=RuntimeError("generation crashed")),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query/", json={"query": "What is RAG?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "What is RAG?"
    assert data["answer"] == ""
    assert data["context_chunks"] == []
    assert data["citations"] == []
    assert data["run_error_msg"] == "generation crashed"
