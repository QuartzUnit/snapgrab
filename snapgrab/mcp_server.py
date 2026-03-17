"""Snapgrab MCP server — screenshot capture tools for Claude Code."""

import json

from fastmcp import FastMCP

from snapgrab.browser import BrowserManager, get_manager
from snapgrab.core import capture
from snapgrab.metadata import extract_metadata

mcp = FastMCP(
    "snapgrab",
    instructions="URL to screenshot with metadata. Claude Vision optimized.",
)

# Shared browser manager for MCP session
_mcp_manager: BrowserManager | None = None


async def _get_mcp_manager() -> BrowserManager:
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = BrowserManager()
    return _mcp_manager


@mcp.tool()
async def capture_screenshot(
    url: str,
    viewport: str = "desktop",
    full_page: bool = False,
    format: str = "png",
    selector: str | None = None,
    wait: str = "networkidle",
    dark_mode: bool = False,
    optimize_vision: bool = True,
) -> str:
    """Capture a screenshot of a web page and return the file path.

    The saved image can be viewed with the Read tool. Also returns
    page metadata (title, OG tags, favicon) and Claude Vision token estimate.

    Args:
        url: URL to capture.
        viewport: "desktop" (1920x1080), "tablet" (768x1024), or "mobile" (375x812).
        full_page: Capture entire scrollable page, not just viewport.
        format: "png" (default, lossless), "jpeg", or "pdf".
        selector: CSS selector to capture a specific element only.
        wait: Wait condition: "networkidle", "domcontentloaded", "load".
        dark_mode: Force dark color scheme.
        optimize_vision: Resize for Claude Vision (1568px max, reduces token cost).
    """
    manager = await _get_mcp_manager()
    result = await capture(
        url,
        viewport=viewport,
        full_page=full_page,
        format=format,
        selector=selector,
        wait=wait,
        dark_mode=dark_mode,
        optimize_vision=optimize_vision,
        _manager=manager,
    )

    return json.dumps({
        "path": result.vision_path or result.path,
        "original_path": result.path,
        "format": result.format,
        "width": result.width,
        "height": result.height,
        "file_size": result.file_size,
        "vision_tokens": result.vision_tokens,
        "processing_time_ms": round(result.processing_time_ms, 1),
        "metadata": {
            "title": result.metadata.title,
            "description": result.metadata.description,
            "og_title": result.metadata.og_title,
            "og_image": result.metadata.og_image,
            "favicon_url": result.metadata.favicon_url,
            "status_code": result.metadata.status_code,
            "url": result.metadata.url,
        },
    }, ensure_ascii=False)


@mcp.tool()
async def capture_comparison(
    url: str,
    viewports: list[str] | None = None,
    full_page: bool = False,
) -> str:
    """Capture screenshots of the same URL in multiple viewports for comparison.

    Useful for responsive design review — compare desktop vs mobile layouts.

    Args:
        url: URL to capture.
        viewports: List of viewports to compare. Default: ["desktop", "mobile"].
        full_page: Capture entire scrollable page for each viewport.
    """
    if viewports is None:
        viewports = ["desktop", "mobile"]

    manager = await _get_mcp_manager()
    captures = []

    for vp in viewports:
        result = await capture(
            url,
            viewport=vp,
            full_page=full_page,
            optimize_vision=True,
            _manager=manager,
        )
        captures.append({
            "viewport": vp,
            "path": result.vision_path or result.path,
            "width": result.width,
            "height": result.height,
            "vision_tokens": result.vision_tokens,
        })

    return json.dumps({
        "url": url,
        "captures": captures,
        "total_vision_tokens": sum(c["vision_tokens"] for c in captures),
    }, ensure_ascii=False)


@mcp.tool()
async def extract_page_metadata(url: str) -> str:
    """Extract page metadata without taking a screenshot.

    Returns title, description, Open Graph tags, favicon URL, and HTTP status.
    Faster than capture_screenshot when you only need metadata.

    Args:
        url: URL to extract metadata from.
    """
    manager = await _get_mcp_manager()
    page = await manager.new_page()
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=30000)
        meta = await extract_metadata(page, response)
        return json.dumps({
            "title": meta.title,
            "description": meta.description,
            "og_title": meta.og_title,
            "og_description": meta.og_description,
            "og_image": meta.og_image,
            "favicon_url": meta.favicon_url,
            "status_code": meta.status_code,
            "content_type": meta.content_type,
            "url": meta.url,
        }, ensure_ascii=False)
    finally:
        await page.context.close()


def main():
    """Run the MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()
