"""Tests for vision.py — Claude Vision optimization."""

import os
import tempfile

from PIL import Image

from snapgrab.vision import MAX_VISION_DIM, estimate_vision_tokens, optimize_for_vision


# === estimate_vision_tokens ===


def test_tokens_small_image():
    """Small image: exact calculation."""
    assert estimate_vision_tokens(750, 750) == 750


def test_tokens_exact_max():
    """Image at exactly max dimension."""
    tokens = estimate_vision_tokens(MAX_VISION_DIM, MAX_VISION_DIM)
    assert tokens == (MAX_VISION_DIM * MAX_VISION_DIM) // 750


def test_tokens_larger_than_max():
    """Image larger than max gets scaled down."""
    tokens = estimate_vision_tokens(3000, 2000)
    # Scale factor: min(1568/3000, 1568/2000) = 0.5227
    # Effective: 1568 x 1045
    assert tokens < (3000 * 2000) // 750
    assert tokens > 0


def test_tokens_wide_image():
    """Very wide image."""
    tokens = estimate_vision_tokens(5000, 500)
    assert tokens > 0
    assert tokens < (5000 * 500) // 750


def test_tokens_tall_image():
    """Very tall image (full-page screenshot)."""
    tokens = estimate_vision_tokens(1920, 10000)
    assert tokens > 0


def test_tokens_tiny_image():
    """Tiny image passes through."""
    assert estimate_vision_tokens(100, 100) == (100 * 100) // 750


def test_tokens_zero():
    """Zero dimensions."""
    assert estimate_vision_tokens(0, 0) == 0


def test_tokens_one_dim_over():
    """Only width exceeds max."""
    tokens = estimate_vision_tokens(3000, 1000)
    assert tokens > 0
    assert tokens <= (MAX_VISION_DIM * MAX_VISION_DIM) // 750


# === optimize_for_vision ===


def test_optimize_small_image_unchanged():
    """Image within limits returns same path."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (800, 600), color="red")
        img.save(f.name)
        result = optimize_for_vision(f.name)
        assert result == f.name
        os.unlink(f.name)


def test_optimize_large_image_resized():
    """Image exceeding limits gets resized."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (3000, 2000), color="blue")
        img.save(f.name)
        result = optimize_for_vision(f.name)
        assert result != f.name
        assert "_vision" in result

        resized = Image.open(result)
        assert resized.width <= MAX_VISION_DIM
        assert resized.height <= MAX_VISION_DIM

        os.unlink(f.name)
        os.unlink(result)


def test_optimize_custom_output_path():
    """Custom output path."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (3000, 2000), color="green")
        img.save(f.name)

        out = f.name.replace(".png", "_custom.png")
        result = optimize_for_vision(f.name, output_path=out)
        assert result == out
        assert os.path.exists(out)

        os.unlink(f.name)
        os.unlink(out)


def test_optimize_preserves_aspect_ratio():
    """Aspect ratio preserved after resize."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (4000, 2000), color="yellow")
        img.save(f.name)
        result = optimize_for_vision(f.name)

        resized = Image.open(result)
        original_ratio = 4000 / 2000
        resized_ratio = resized.width / resized.height
        assert abs(original_ratio - resized_ratio) < 0.01

        os.unlink(f.name)
        os.unlink(result)
