"""
Duplicate / spam detection — checks whether a new complaint is likely the
same real-world issue as an already-open complaint, using location distance
+ image similarity. Prevents the same pothole being logged as 10 separate
complaints.

This works against REAL complaint history passed in by the caller (your
backend queries the database and passes the results here) — this module
does not fabricate or assume any history of its own.

Two signals combined:
- Distance: haversine formula (great-circle distance between two lat/lng
  points), no external mapping API needed.
- Image similarity: perceptual hash (average hash) — robust to small
  compression/lighting differences, unlike exact byte comparison.
"""

import math
from PIL import Image
import imagehash

DEFAULT_RADIUS_METERS = 50.0
DEFAULT_IMAGE_HASH_THRESHOLD = 10  # lower = stricter match; 0-64 possible range


def haversine_distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two GPS points, in meters."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def image_similarity_score(image_path_a: str, image_path_b: str) -> int:
    """
    Returns the Hamming distance between the two images' perceptual hashes.
    Lower = more similar. 0 means near-identical images.
    """
    hash_a = imagehash.average_hash(Image.open(image_path_a))
    hash_b = imagehash.average_hash(Image.open(image_path_b))
    return hash_a - hash_b


def find_duplicate(
    new_complaint: dict,
    existing_complaints: list[dict],
    radius_meters: float = DEFAULT_RADIUS_METERS,
    image_hash_threshold: int = DEFAULT_IMAGE_HASH_THRESHOLD,
) -> dict | None:
    """
    new_complaint: {"latitude": .., "longitude": .., "image_path": .., "category": ..}
    existing_complaints: list of dicts with the same shape, plus "id" and "status",
                          pulled from your real database — not sample data.

    Only compares against complaints that are NOT resolved (open issues).
    For resolved issues reappearing, see recurrence_detection.py instead.

    Returns the matching complaint dict (with an added "similarity" score)
    if a likely duplicate is found, else None.
    """
    lat, lng = new_complaint["latitude"], new_complaint["longitude"]
    category = new_complaint.get("category")

    for existing in existing_complaints:
        if existing.get("status") == "resolved":
            continue
        if category and existing.get("category") and existing["category"] != category:
            continue

        distance = haversine_distance_meters(lat, lng, existing["latitude"], existing["longitude"])
        if distance > radius_meters:
            continue

        try:
            similarity = image_similarity_score(new_complaint["image_path"], existing["image_path"])
        except (FileNotFoundError, OSError):
            similarity = None

        if similarity is None or similarity <= image_hash_threshold:
            return {**existing, "distance_meters": round(distance, 1), "similarity": similarity}

    return None


if __name__ == "__main__":
    print("This module is meant to be imported and called with real complaint data.")
    print("Example: find_duplicate(new_complaint, existing_complaints_from_db)")
