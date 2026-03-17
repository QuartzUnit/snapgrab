"""Extract page metadata (title, OG tags, favicon, status)."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin

from playwright.async_api import Page, Response


@dataclass
class CaptureMetadata:
    """Metadata extracted from a web page."""

    title: str = ""
    description: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    favicon_url: str = ""
    status_code: int = 0
    content_type: str = ""
    url: str = ""


async def extract_metadata(page: Page, response: Response | None = None) -> CaptureMetadata:
    """Extract metadata from a loaded page."""
    meta = CaptureMetadata()

    if response:
        meta.status_code = response.status
        meta.content_type = response.headers.get("content-type", "")
        meta.url = response.url

    meta.title = await _safe_eval(page, "document.title") or ""

    meta.description = await _safe_eval(
        page, "document.querySelector('meta[name=\"description\"]')?.content"
    ) or ""

    meta.og_title = await _safe_eval(
        page, "document.querySelector('meta[property=\"og:title\"]')?.content"
    ) or ""

    meta.og_description = await _safe_eval(
        page, "document.querySelector('meta[property=\"og:description\"]')?.content"
    ) or ""

    meta.og_image = await _safe_eval(
        page, "document.querySelector('meta[property=\"og:image\"]')?.content"
    ) or ""

    favicon_href = await _safe_eval(
        page,
        "document.querySelector('link[rel=\"icon\"]')?.href || "
        "document.querySelector('link[rel=\"shortcut icon\"]')?.href",
    )
    if favicon_href:
        meta.favicon_url = favicon_href
    elif meta.url:
        meta.favicon_url = urljoin(meta.url, "/favicon.ico")

    return meta


async def _safe_eval(page: Page, expression: str) -> str | None:
    """Evaluate JS expression, return None on error."""
    try:
        result = await page.evaluate(expression)
        return result if isinstance(result, str) else None
    except Exception:
        return None
