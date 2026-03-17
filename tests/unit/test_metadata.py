"""Tests for metadata.py — page metadata extraction."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from snapgrab.metadata import CaptureMetadata, extract_metadata


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.evaluate = AsyncMock(return_value=None)
    return page


@pytest.fixture
def mock_response():
    resp = MagicMock()
    resp.status = 200
    resp.url = "https://example.com/"
    resp.headers = {"content-type": "text/html; charset=utf-8"}
    return resp


async def test_metadata_from_response(mock_page, mock_response):
    """Status code and URL from response."""
    meta = await extract_metadata(mock_page, mock_response)
    assert meta.status_code == 200
    assert meta.url == "https://example.com/"
    assert meta.content_type == "text/html; charset=utf-8"


async def test_metadata_no_response(mock_page):
    """No response — defaults to empty."""
    meta = await extract_metadata(mock_page)
    assert meta.status_code == 0
    assert meta.url == ""


async def test_metadata_title(mock_page, mock_response):
    """Title extracted from document.title."""
    call_count = 0

    async def eval_side_effect(expr):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # document.title
            return "Example Page"
        return None

    mock_page.evaluate = eval_side_effect
    meta = await extract_metadata(mock_page, mock_response)
    assert meta.title == "Example Page"


async def test_metadata_og_tags(mock_page, mock_response):
    """OG tags extracted."""
    values = {
        "document.title": "Page Title",
        'meta[name="description"]': "A description",
        'meta[property="og:title"]': "OG Title",
        'meta[property="og:description"]': "OG Desc",
        'meta[property="og:image"]': "https://example.com/og.png",
    }

    async def eval_side_effect(expr):
        for key, val in values.items():
            if key in expr:
                return val
        return None

    mock_page.evaluate = eval_side_effect
    meta = await extract_metadata(mock_page, mock_response)
    assert meta.og_title == "OG Title"
    assert meta.og_image == "https://example.com/og.png"


async def test_metadata_favicon_fallback(mock_page, mock_response):
    """Favicon falls back to /favicon.ico."""
    mock_page.evaluate = AsyncMock(return_value=None)
    meta = await extract_metadata(mock_page, mock_response)
    assert meta.favicon_url == "https://example.com/favicon.ico"


async def test_metadata_eval_error(mock_page, mock_response):
    """JS evaluation errors handled gracefully."""
    mock_page.evaluate = AsyncMock(side_effect=Exception("eval failed"))
    meta = await extract_metadata(mock_page, mock_response)
    assert meta.title == ""
    assert meta.description == ""


def test_capture_metadata_defaults():
    """CaptureMetadata defaults."""
    meta = CaptureMetadata()
    assert meta.title == ""
    assert meta.status_code == 0
    assert meta.og_image == ""
