"""Object storage connection for Cloudflare R2."""

from __future__ import annotations

import logging
from contextlib import AbstractAsyncContextManager
from os import getenv
from typing import TYPE_CHECKING

from aioboto3 import Session

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client

logger = logging.getLogger(__name__)

_session = Session()


def obj_store_client() -> AbstractAsyncContextManager[S3Client]:
    """Create an async S3 client context manager for Cloudflare R2."""
    logger.debug("Creating Cloudflare R2 S3 client")
    return _session.client(
        service_name="s3",
        endpoint_url=f"https://{getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )
