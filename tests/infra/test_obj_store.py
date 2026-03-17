"""Smoke tests for the in-memory object store stub."""

import pytest

from tests.stubs.obj_store_stub import ObjStoreStubClient, make_obj_store_stub


async def test_put_and_get_object():
    """Stored objects are retrievable with correct body and content type."""
    client = ObjStoreStubClient()
    await client.put_object(
        Bucket="test-bucket",
        Key="test.md",
        Body="# Hello",
        ContentType="text/markdown",
    )
    obj = await client.get_object(Bucket="test-bucket", Key="test.md")
    assert obj["Body"] == "# Hello"
    assert obj["ContentType"] == "text/markdown"


async def test_get_missing_key_raises():
    """Requesting a nonexistent key raises KeyError."""
    client = ObjStoreStubClient()
    with pytest.raises(KeyError, match="missing"):
        await client.get_object(Bucket="b", Key="missing")


async def test_put_overwrites_existing():
    """A second put to the same key overwrites the previous value."""
    client = ObjStoreStubClient()
    await client.put_object(Bucket="b", Key="k", Body="v1", ContentType="text/plain")
    await client.put_object(Bucket="b", Key="k", Body="v2", ContentType="text/plain")
    obj = await client.get_object(Bucket="b", Key="k")
    assert obj["Body"] == "v2"


async def test_stub_factory_yields_same_client():
    """The factory context manager yields the original client instance."""
    client = ObjStoreStubClient()
    factory = make_obj_store_stub(client)
    async with factory() as c:
        assert c is client
