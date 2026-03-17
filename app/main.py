"""Application entrypoint for the FastAPI RAG service."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.main import api_router
from app.config import LOG_FILEMODE, LOG_FILENAME, LOG_LEVEL
from app.infra.qdrant import init_vec_db
from app.infra.supabase import init_rel_db
from app.logging_config import config_logging

config_logging(LOG_LEVEL, LOG_FILENAME, LOG_FILEMODE)

load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Initializes database services on startup.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Control returns to FastAPI during application runtime.
    """
    logger.info("Application startup")
    try:
        await init_vec_db()
        await init_rel_db()
        logger.debug("Application startup complete")
        yield
    except Exception:
        logger.exception("Application startup failed")
        raise
    finally:
        logger.debug("Application shutdown")


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)


@app.get("/health", tags=["health"])
def read_health() -> dict[str, str]:
    """Return application health status.

    Returns:
        A dictionary indicating the health status of the application.
    """
    return {"status": "ok"}
