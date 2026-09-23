"""
Image quality check — runs BEFORE a photo reaches the YOLO model.
Rejects or flags photos that are too blurry or too dark to be useful,
so garbage submissions don't pollute detection results or training data.

Uses classic, well-understood image processing (no ML model needed here):
- Blur: variance of the Laplacian. Sharp images have high-frequency edges,
  which the Laplacian responds to strongly -> high variance. Blurry images
  have smoothed-out edges -> low variance.
- Darkness: mean pixel brightness on the grayscale image.

Thresholds below are reasonable starting points, not tuned on your real
data yet. If you find real submissions getting wrongly flagged or wrongly
passed, adjust BLUR_THRESHOLD / DARKNESS_THRESHOLD based on examples.
"""

import cv2

BLUR_THRESHOLD = 100.0       # below this = too blurry
DARKNESS_THRESHOLD = 40.0    # below this (0-255 scale) = too dark
BRIGHTNESS_THRESHOLD = 240.0 # above this = blown out / overexposed


def check_image_quality(image_path: str) -> dict:
    """
    Returns a dict describing whether the image passes quality checks.

    {
        "status": "ok" | "too_blurry" | "too_dark" | "too_bright" | "unreadable",
        "blur_score": float | None,
        "brightness": float | None,
    }

    Never raises for a bad/corrupt image — returns "unreadable" instead,
    so the caller can show a clear message rather than crashing.
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"status": "unreadable", "blur_score": None, "brightness": None}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())

    if blur_score < BLUR_THRESHOLD:
        status = "too_blurry"
    elif brightness < DARKNESS_THRESHOLD:
        status = "too_dark"
    elif brightness > BRIGHTNESS_THRESHOLD:
        status = "too_bright"
    else:
        status = "ok"

    return {"status": status, "blur_score": round(blur_score, 1), "brightness": round(brightness, 1)}


def check_images(image_paths: list[str]) -> list[dict]:
    """Runs check_image_quality on a batch, tagging each result with its path."""
    results = []
    for path in image_paths:
        result = check_image_quality(path)
        result["path"] = path
        results.append(result)
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python image_quality.py <image_path> [image_path ...]")
        sys.exit(1)
    for path in sys.argv[1:]:
        print(path, "->", check_image_quality(path))
