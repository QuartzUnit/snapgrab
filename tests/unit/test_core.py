"""Tests for core.py — CaptureResult and utility logic."""

from snapgrab.core import CaptureResult, DEFAULT_OUTPUT_DIR
from snapgrab.metadata import CaptureMetadata
from snapgrab.browser import VIEWPORTS


def test_capture_result_defaults():
    """CaptureResult has sensible defaults."""
    r = CaptureResult()
    assert r.path == ""
    assert r.format == "png"
    assert r.width == 0
    assert r.height == 0
    assert r.file_size == 0
    assert r.vision_tokens == 0
    assert isinstance(r.metadata, CaptureMetadata)


def test_capture_result_with_metadata():
    """CaptureResult stores metadata."""
    meta = CaptureMetadata(title="Test", status_code=200)
    r = CaptureResult(path="/tmp/test.png", metadata=meta)
    assert r.metadata.title == "Test"
    assert r.metadata.status_code == 200


def test_default_output_dir():
    assert DEFAULT_OUTPUT_DIR == "/tmp/snapgrab"


def test_viewports_presets():
    """Viewport presets exist."""
    assert "desktop" in VIEWPORTS
    assert "tablet" in VIEWPORTS
    assert "mobile" in VIEWPORTS
    assert VIEWPORTS["desktop"]["width"] == 1920
    assert VIEWPORTS["mobile"]["width"] == 375


def test_viewports_have_both_dimensions():
    for name, vp in VIEWPORTS.items():
        assert "width" in vp, f"{name} missing width"
        assert "height" in vp, f"{name} missing height"
        assert vp["width"] > 0
        assert vp["height"] > 0
