"""
Auto-generated complaint description — builds a plain-English description
from what the YOLO model actually detected, so citizens don't have to type
one themselves.

This is template-based, not a language model. It's honest about that: it
only ever states what the detection dict actually contains. If a field
(size, confidence) is missing, it's left out of the sentence rather than
guessed.
"""


def _size_label(relative_size: float | None) -> str | None:
    """Converts a 0-1 relative bounding-box-area score into a plain word.
    This is a RELATIVE size only (see depth/size estimation notes) — never
    a physical measurement."""
    if relative_size is None:
        return None
    if relative_size < 0.05:
        return "small"
    if relative_size < 0.15:
        return "moderate"
    return "large"


def generate_description(detection: dict) -> str:
    """
    detection is expected to look like:
    {
        "category": "pothole",
        "confidence": 0.87,
        "relative_size": 0.09,   # optional
    }

    Returns a short, honest sentence describing the detection.
    Never invents values that aren't in the input dict.
    """
    category = detection.get("category")
    if not category:
        return "Issue detected — category not identified."

    category_label = category.replace("_", " ")
    parts = [f"{category_label.capitalize()} detected"]

    size_label = _size_label(detection.get("relative_size"))
    if size_label:
        parts.append(f"{size_label} size")

    confidence = detection.get("confidence")
    if confidence is not None:
        parts.append(f"{confidence * 100:.0f}% confidence")

    return ", ".join(parts) + "."


def generate_description_for_multiple(detections: list[dict]) -> str:
    """When a photo has more than one detection, summarizes all of them."""
    if not detections:
        return "No issues detected in the submitted photo."
    if len(detections) == 1:
        return generate_description(detections[0])

    sentences = [generate_description(d) for d in detections]
    return f"{len(detections)} issues detected: " + " ".join(sentences)


if __name__ == "__main__":
    example = {"category": "pothole", "confidence": 0.87, "relative_size": 0.12}
    print(generate_description(example))
