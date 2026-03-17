"""Core capture logic — the main orchestrator."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from snapgrab.browser import BrowserManager, close_manager, get_manager
from snapgrab.metadata import CaptureMetadata, extract_metadata
from snapgrab.vision import estimate_vision_tokens, optimize_for_vision

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = "/tmp/snapgrab"


@dataclass
class CaptureResult:
    """Result of a screenshot capture."""

    path: str = ""
    format: str = "png"
    width: int = 0
    height: int = 0
    file_size: int = 0
    metadata: CaptureMetadata = field(default_factory=CaptureMetadata)
    vision_tokens: int = 0
    vision_path: str = ""
    processing_time_ms: float = 0.0


async def capture(
    url: str,
    *,
    viewport: str | tuple[int, int] = "desktop",
    full_page: bool = False,
    format: str = "png",
    selector: str | None = None,
    wait: str | float = "networkidle",
    dark_mode: bool = False,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    quality: int | None = None,
    optimize_vision: bool = True,
    headers: dict[str, str] | None = None,
    _manager: BrowserManager | None = None,
) -> CaptureResult:
    """Capture a screenshot of a URL.

    Args:
        url: Target URL to capture.
        viewport: "desktop", "tablet", "mobile", or (width, height) tuple.
        full_page: Capture entire scrollable page.
        format: "png" (default), "jpeg", or "pdf".
        selector: CSS selector to capture specific element.
        wait: Wait condition: "networkidle", "domcontentloaded", "load", or seconds (float).
        dark_mode: Force dark color scheme.
        output_dir: Directory to save screenshots.
        quality: JPEG quality 0-100 (ignored for PNG/PDF).
        optimize_vision: Resize for Claude Vision (1568px max).
        headers: Extra HTTP headers.
        _manager: BrowserManager instance (for reuse in MCP server).
    """
    start = time.monotonic()
    result = CaptureResult(format=format)

    # Ensure output directory
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    domain = urlparse(url).netloc.replace(".", "_").replace(":", "_")
    ts = time.strftime("%Y%m%d_%H%M%S")
    vp_label = viewport if isinstance(viewport, str) else f"{viewport[0]}x{viewport[1]}"
    filename = f"{domain}_{vp_label}_{ts}.{format}"
    filepath = out_dir / filename

    # Browser
    manager = _manager or await get_manager()
    own_manager = _manager is None
    page = await manager.new_page(viewport=viewport, dark_mode=dark_mode, extra_headers=headers)

    try:
        # Navigate
        wait_until = "networkidle"
        if isinstance(wait, str) and wait in ("networkidle", "domcontentloaded", "load"):
            wait_until = wait
        elif isinstance(wait, str):
            wait_until = "load"

        response = await page.goto(url, wait_until=wait_until, timeout=30000)

        # Extra delay if wait is a number
        if isinstance(wait, (int, float)) and wait > 0:
            await page.wait_for_timeout(int(wait * 1000))

        # Scroll to trigger lazy loading for full_page
        if full_page:
            await page.evaluate("""
                async () => {
                    const delay = ms => new Promise(r => setTimeout(r, ms));
                    for (let i = 0; i < document.body.scrollHeight; i += window.innerHeight) {
                        window.scrollTo(0, i);
                        await delay(100);
                    }
                    window.scrollTo(0, 0);
                }
            """)
            await page.wait_for_timeout(500)

        # Extract metadata
        result.metadata = await extract_metadata(page, response)

        # Capture
        screenshot_opts: dict = {"path": str(filepath), "full_page": full_page}

        if format == "jpeg":
            screenshot_opts["type"] = "jpeg"
            screenshot_opts["quality"] = quality or 80
        elif format == "pdf":
            await page.pdf(path=str(filepath))
        else:
            screenshot_opts["type"] = "png"

        if selector:
            element = await page.query_selector(selector)
            if element:
                if format != "pdf":
                    await element.screenshot(**screenshot_opts)
            else:
                logger.warning("Selector '%s' not found, capturing full page", selector)
                if format != "pdf":
                    await page.screenshot(**screenshot_opts)
        elif format != "pdf":
            await page.screenshot(**screenshot_opts)

        # Get dimensions
        vp = await page.evaluate("() => ({ w: window.innerWidth, h: window.innerHeight })")
        result.width = vp["w"]
        if full_page:
            body_h = await page.evaluate("() => document.body.scrollHeight")
            result.height = body_h
        else:
            result.height = vp["h"]

        result.path = str(filepath)
        result.file_size = filepath.stat().st_size

        # Vision optimization
        if optimize_vision and format in ("png", "jpeg"):
            result.vision_path = optimize_for_vision(str(filepath))
            from PIL import Image

            with Image.open(result.vision_path) as img:
                vw, vh = img.size
            result.vision_tokens = estimate_vision_tokens(vw, vh)
        else:
            result.vision_tokens = estimate_vision_tokens(result.width, result.height)

    finally:
        await page.context.close()
        if own_manager:
            await close_manager()

    result.processing_time_ms = (time.monotonic() - start) * 1000
    return result
