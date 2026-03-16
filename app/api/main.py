"""API router aggregator."""

from fastapi import APIRouter

from app.api.routes import crawl

api_router = APIRouter()
api_router.include_router(crawl.router)
