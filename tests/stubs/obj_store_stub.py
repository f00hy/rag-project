"""In-memory stub for object storage (Cloudflare R2)."""

from contextlib import asynccontextmanager


class ObjStoreStubClient:
    """Minimal async S3-compatible client backed by an in-memory dictionary."""

    def __init__(self) -> None:
        """Create an empty in-memory object store."""
        self.objects: dict[tuple[str, str], dict[str, str]] = {}

    async def put_object(self, **kwargs: str) -> None:
        """Store an object keyed by (Bucket, Key)."""
        bucket = kwargs.get("Bucket", "")
        key = kwargs.get("Key", "")
        self.objects[(bucket, key)] = {
            "Body": kwargs.get("Body", ""),
            "ContentType": kwargs.get("ContentType", ""),
        }

    async def get_object(self, **kwargs: str) -> dict[str, str]:
        """Retrieve an object by (Bucket, Key), raising KeyError if absent."""
        bucket = kwargs.get("Bucket", "")
        key = kwargs.get("Key", "")
        if (bucket, key) not in self.objects:
            raise KeyError(f"NoSuchKey: {key}")
        return self.objects[(bucket, key)]


def make_obj_store_stub(client: ObjStoreStubClient):
    """Return a factory matching the ``obj_store_client()`` signature."""

    @asynccontextmanager
    async def _factory():
        yield client

    return _factory
