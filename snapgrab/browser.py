"""Playwright browser lifecycle management."""

from __future__ import annotations

import logging
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

logger = logging.getLogger(__name__)

VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 375, "height": 812},
}


class BrowserManager:
    """Manage Playwright browser lifecycle.

    Supports reuse across multiple captures (MCP server mode)
    or single-shot usage (CLI/API mode).
    """

    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None

    async def _ensure_browser(self) -> Browser:
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            logger.debug("Browser launched")
        return self._browser

    async def new_page(
        self,
        viewport: str | tuple[int, int] = "desktop",
        dark_mode: bool = False,
        extra_headers: dict[str, str] | None = None,
    ) -> Page:
        """Create a new page with viewport and color scheme."""
        browser = await self._ensure_browser()

        if isinstance(viewport, str):
            vp = VIEWPORTS.get(viewport, VIEWPORTS["desktop"])
        else:
            vp = {"width": viewport[0], "height": viewport[1]}

        context_opts: dict[str, Any] = {
            "viewport": vp,
            "color_scheme": "dark" if dark_mode else "light",
        }
        if extra_headers:
            context_opts["extra_http_headers"] = extra_headers

        context: BrowserContext = await browser.new_context(**context_opts)
        page = await context.new_page()
        return page

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.debug("Browser closed")


# Module-level singleton for MCP server reuse
_manager: BrowserManager | None = None


async def get_manager() -> BrowserManager:
    global _manager
    if _manager is None:
        _manager = BrowserManager()
    return _manager


async def close_manager() -> None:
    global _manager
    if _manager:
        await _manager.close()
        _manager = None
