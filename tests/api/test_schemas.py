"""Tests for API request and response schemas."""

from typing import cast

import pytest
from pydantic import TypeAdapter, ValidationError
from pydantic.networks import HttpUrl

from app.api.schemas import CrawlFailure, CrawlRequest, CrawlResponse
from app.config import MAX_PAGES

HTTP_URL = TypeAdapter(HttpUrl).validate_python


def test_crawl_request_valid_with_defaults():
    """A valid URL produces a CrawlRequest with the default max_pages."""
    req = CrawlRequest(url=HTTP_URL("https://example.com"))
    assert str(req.url).rstrip("/") == "https://example.com"
    assert req.max_pages == MAX_PAGES


def test_crawl_request_custom_max_pages():
    """max_pages can be overridden."""
    req = CrawlRequest(url=HTTP_URL("https://example.com"), max_pages=5)
    assert req.max_pages == 5


def test_crawl_request_invalid_url():
    """An invalid URL raises a validation error."""
    with pytest.raises(ValidationError):
        CrawlRequest(url=cast(HttpUrl, "not-a-url"))


def test_crawl_response_minimal():
    """CrawlResponse works with only required fields."""
    resp = CrawlResponse(url=HTTP_URL("https://example.com"), pages_crawled=3)
    assert resp.pages_crawled == 3
    assert resp.failures == []
    assert resp.run_error_msg is None


def test_crawl_response_with_failures():
    """CrawlResponse correctly stores failure details."""
    resp = CrawlResponse(
        url=HTTP_URL("https://example.com"),
        pages_crawled=1,
        failures=[
            CrawlFailure(url=HTTP_URL("https://example.com/bad"), error_msg="404"),
        ],
        run_error_msg=None,
    )
    assert len(resp.failures) == 1
    assert resp.failures[0].error_msg == "404"


def test_crawl_failure_optional_error():
    """CrawlFailure.error_msg defaults to None."""
    fail = CrawlFailure(url=HTTP_URL("https://example.com/page"))
    assert fail.error_msg is None
