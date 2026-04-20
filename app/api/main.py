"""API router aggregator."""

from fastapi import APIRouter

from app.api.routes import crawl, query

api_router = APIRouter()
api_router.include_router(crawl.router)
api_router.include_router(query.router)
