"""Claude Vision optimization — resize and token estimation."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

# Claude Vision max effective resolution
MAX_VISION_DIM = 1568


def estimate_vision_tokens(width: int, height: int) -> int:
    """Estimate Claude Vision token cost for an image.

    Claude downscales images exceeding 1568px on either dimension.
    Token cost = (effective_width * effective_height) / 750
    """
    ew = min(width, MAX_VISION_DIM)
    eh = min(height, MAX_VISION_DIM)

    if width > MAX_VISION_DIM or height > MAX_VISION_DIM:
        ratio = min(MAX_VISION_DIM / width, MAX_VISION_DIM / height)
        ew = int(width * ratio)
        eh = int(height * ratio)

    return (ew * eh) // 750


def optimize_for_vision(image_path: str, output_path: str | None = None) -> str:
    """Resize image to fit within Claude Vision limits.

    Saves optimized version alongside original if output_path not specified.
    Returns path to optimized image.
    """
    img = Image.open(image_path)
    w, h = img.size

    if w <= MAX_VISION_DIM and h <= MAX_VISION_DIM:
        return image_path

    ratio = min(MAX_VISION_DIM / w, MAX_VISION_DIM / h)
    new_w = int(w * ratio)
    new_h = int(h * ratio)

    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if output_path is None:
        p = Path(image_path)
        output_path = str(p.with_stem(f"{p.stem}_vision"))

    img_resized.save(output_path)
    return output_path
