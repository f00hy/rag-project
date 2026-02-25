"""Object storage connection for Cloudflare R2."""

from contextlib import AbstractAsyncContextManager
from os import getenv

from aioboto3 import Session
from types_aiobotocore_s3 import S3Client

_session = Session()


def obj_store_client() -> AbstractAsyncContextManager[S3Client]:
    """Create an async S3 client context manager for Cloudflare R2."""
    return _session.client(
        service_name="s3",
        endpoint_url=f"https://{getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )
