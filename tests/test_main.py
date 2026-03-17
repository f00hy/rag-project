"""Tests for the application entrypoint and wiring."""

from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient


@patch("app.main.init_rel_db", new_callable=AsyncMock)
@patch("app.main.init_vec_db", new_callable=AsyncMock)
async def test_health_endpoint(mock_init_vec, mock_init_rel):
    """The /health endpoint returns an ok status."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("app.main.init_rel_db", new_callable=AsyncMock)
@patch("app.main.init_vec_db", new_callable=AsyncMock)
async def test_crawl_route_registered(mock_init_vec, mock_init_rel):
    """The /crawl/ route is registered on the application."""
    from app.main import app

    route_paths = [route.path for route in app.routes if hasattr(route, "path")]
    assert "/crawl/" in route_paths


@patch("app.main.init_rel_db", new_callable=AsyncMock)
@patch("app.main.init_vec_db", new_callable=AsyncMock)
async def test_health_route_registered(mock_init_vec, mock_init_rel):
    """The /health route is registered on the application."""
    from app.main import app

    route_paths = [route.path for route in app.routes if hasattr(route, "path")]
    assert "/health" in route_paths
