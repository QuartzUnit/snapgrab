"""CLI entry point — python -m snapgrab or `snapgrab` command."""

import asyncio
import json
import sys

import click
from rich.console import Console
from rich.table import Table

from snapgrab import __version__
from snapgrab.core import capture

console = Console()


@click.group()
@click.version_option(__version__, prog_name="snapgrab")
def main():
    """Snapgrab — URL to screenshot with metadata."""


@main.command("capture", hidden=True)
@click.argument("url")
@click.pass_context
def capture_alias(ctx, url):
    """Alias for default capture."""
    ctx.invoke(capture_cmd, url=url)


@main.command("url")
@click.argument("url")
@click.option("--viewport", "-v", default="desktop", help="Viewport: desktop, tablet, mobile, or WxH")
@click.option("--full-page", "-f", is_flag=True, help="Capture entire scrollable page")
@click.option("--format", "fmt", default="png", type=click.Choice(["png", "jpeg", "pdf"]), help="Output format")
@click.option("--selector", "-s", help="CSS selector to capture")
@click.option("--wait", "-w", default="networkidle", help="Wait: networkidle, domcontentloaded, load, or seconds")
@click.option("--dark-mode", "-d", is_flag=True, help="Force dark color scheme")
@click.option("--output", "-o", default="/tmp/snapgrab", help="Output directory")
@click.option("--quality", "-q", type=int, help="JPEG quality (0-100)")
@click.option("--no-optimize", is_flag=True, help="Skip Claude Vision optimization")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def capture_cmd(url, viewport, full_page, fmt, selector, wait, dark_mode, output, quality, no_optimize, json_output):
    """Capture a screenshot of a URL."""
    vp = viewport
    if "x" in viewport.lower() and viewport not in ("desktop", "tablet", "mobile"):
        parts = viewport.lower().split("x")
        vp = (int(parts[0]), int(parts[1]))

    wait_val: str | float = wait
    try:
        wait_val = float(wait)
    except ValueError:
        pass

    try:
        result = asyncio.run(capture(
            url,
            viewport=vp,
            full_page=full_page,
            format=fmt,
            selector=selector,
            wait=wait_val,
            dark_mode=dark_mode,
            output_dir=output,
            quality=quality,
            optimize_vision=not no_optimize,
        ))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if json_output:
        output_data = {
            "path": result.path,
            "format": result.format,
            "width": result.width,
            "height": result.height,
            "file_size": result.file_size,
            "vision_tokens": result.vision_tokens,
            "vision_path": result.vision_path,
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
        }
        click.echo(json.dumps(output_data, ensure_ascii=False, indent=2))
    else:
        console.print(f"[green]✓[/green] Saved to [bold]{result.path}[/bold]")
        console.print(f"  {result.width}x{result.height} {result.format.upper()} ({result.file_size:,} bytes)")
        if result.metadata.title:
            console.print(f"  Title: {result.metadata.title}")
        console.print(f"  Vision tokens: ~{result.vision_tokens:,}")
        console.print(f"  Time: {result.processing_time_ms:.0f}ms")


@main.command()
@click.argument("url")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def meta(url, json_output):
    """Extract page metadata only (no screenshot)."""
    from snapgrab.browser import BrowserManager
    from snapgrab.metadata import extract_metadata

    async def _extract():
        mgr = BrowserManager()
        page = await mgr.new_page()
        try:
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            return await extract_metadata(page, response)
        finally:
            await page.context.close()
            await mgr.close()

    try:
        metadata = asyncio.run(_extract())
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if json_output:
        click.echo(json.dumps({
            "title": metadata.title,
            "description": metadata.description,
            "og_title": metadata.og_title,
            "og_description": metadata.og_description,
            "og_image": metadata.og_image,
            "favicon_url": metadata.favicon_url,
            "status_code": metadata.status_code,
            "url": metadata.url,
        }, ensure_ascii=False, indent=2))
    else:
        table = Table(title=f"Metadata: {url}")
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        table.add_row("Title", metadata.title)
        table.add_row("Description", metadata.description[:100] + ("..." if len(metadata.description) > 100 else ""))
        table.add_row("OG Title", metadata.og_title)
        table.add_row("OG Image", metadata.og_image)
        table.add_row("Favicon", metadata.favicon_url)
        table.add_row("Status", str(metadata.status_code))
        table.add_row("URL", metadata.url)
        console.print(table)


if __name__ == "__main__":
    main()
