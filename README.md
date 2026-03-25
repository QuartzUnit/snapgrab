# Snapgrab

[![PyPI](https://img.shields.io/pypi/v/snapgrab)](https://pypi.org/project/snapgrab/)
[![Python](https://img.shields.io/pypi/pyversions/snapgrab)](https://pypi.org/project/snapgrab/)
[![License](https://img.shields.io/github/license/QuartzUnit/snapgrab)](https://github.com/QuartzUnit/snapgrab/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen)]()

> [한국어 문서](README.ko.md)

> URL to screenshot with metadata. Claude Vision optimized.

```python
from snapgrab import capture

result = await capture("https://example.com")
print(result.path)           # /tmp/snapgrab/example_com_desktop_20260317_120000.png
print(result.metadata.title) # "Example Domain"
print(result.vision_tokens)  # ~2764
```

## Features

- **Screenshot capture** — PNG, JPEG, PDF with full-page support
- **Page metadata** — title, description, Open Graph tags, favicon, HTTP status
- **Claude Vision optimized** — auto-resize to 1568px, token cost estimation
- **Viewport presets** — desktop (1920x1080), tablet (768x1024), mobile (375x812)
- **MCP server included** — 3 tools for Claude Code / MCP clients
- **Element capture** — screenshot specific CSS selectors
- **Dark mode** — force light/dark color scheme

## Install

```bash
pip install snapgrab
```

First run will prompt to install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### Python API

```python
import asyncio
from snapgrab import capture

async def main():
    # Basic screenshot
    result = await capture("https://example.com")

    # Mobile viewport, full page
    result = await capture("https://example.com", viewport="mobile", full_page=True)

    # Dark mode, JPEG format
    result = await capture("https://example.com", dark_mode=True, format="jpeg")

    # Specific element
    result = await capture("https://example.com", selector="#main-content")

    # Custom viewport
    result = await capture("https://example.com", viewport=(1440, 900))

asyncio.run(main())
```

### CLI

```bash
snapgrab https://example.com                          # basic PNG
snapgrab https://example.com -v mobile -f             # mobile, full page
snapgrab https://example.com --format jpeg -q 90      # JPEG quality 90
snapgrab https://example.com -s "#hero" --dark-mode   # element + dark mode
snapgrab https://example.com -j                       # JSON output
snapgrab meta https://example.com                     # metadata only
```

### MCP Server

```bash
pip install "snapgrab[mcp]"
snapgrab-mcp  # starts stdio MCP server
```

**Tools:**
- `capture_screenshot` — capture URL with metadata and vision token estimate
- `capture_comparison` — compare desktop vs mobile (or any viewports)
- `extract_page_metadata` — metadata only, no screenshot

## CaptureResult

```python
result.path            # saved file path
result.format          # "png", "jpeg", "pdf"
result.width           # viewport width
result.height          # page height (full_page) or viewport height
result.file_size       # bytes
result.vision_tokens   # estimated Claude Vision token cost
result.vision_path     # path to Vision-optimized image (≤1568px)
result.processing_time_ms
result.metadata.title
result.metadata.description
result.metadata.og_title
result.metadata.og_image
result.metadata.favicon_url
result.metadata.status_code
result.metadata.url    # final URL after redirects
```

## License

[MIT](LICENSE)

<!-- mcp-name: io.github.QuartzUnit/snapgrab -->
