"""
Recurrence detection — flags when an issue reappears at (roughly) the same
location AFTER a previous complaint there was marked "resolved". Different
from duplicate detection (which only checks currently-open complaints):
recurrence means "we thought this was fixed, but it's back".

Reuses the same distance + image-similarity helpers as duplicate_detection.
"""

from duplicate_detection import haversine_distance_meters, image_similarity_score

DEFAULT_RADIUS_METERS = 50.0
DEFAULT_IMAGE_HASH_THRESHOLD = 12  # slightly looser than duplicate check —
                                     # repairs can visibly change the surface


def find_recurrence(
    new_complaint: dict,
    resolved_complaints: list[dict],
    radius_meters: float = DEFAULT_RADIUS_METERS,
    image_hash_threshold: int = DEFAULT_IMAGE_HASH_THRESHOLD,
) -> dict | None:
    """
    new_complaint: {"latitude": .., "longitude": .., "image_path": .., "category": ..}
    resolved_complaints: complaints from your real database where status == "resolved",
                          ideally with a "resolved_at" timestamp.

    Returns the matching resolved complaint (flagged as a likely recurrence)
    if the new complaint is at the same spot and same category, else None.

    Image similarity is a supporting signal, not a hard requirement — a
    repaired-then-broken-again pothole may look different after repair, so
    location + category match alone can be enough to flag for human review.
    """
    lat, lng = new_complaint["latitude"], new_complaint["longitude"]
    category = new_complaint.get("category")

    candidates = []
    for resolved in resolved_complaints:
        if category and resolved.get("category") and resolved["category"] != category:
            continue

        distance = haversine_distance_meters(lat, lng, resolved["latitude"], resolved["longitude"])
        if distance > radius_meters:
            continue

        similarity = None
        try:
            similarity = image_similarity_score(new_complaint["image_path"], resolved["image_path"])
        except (FileNotFoundError, OSError, KeyError):
            pass

        candidates.append({**resolved, "distance_meters": round(distance, 1), "similarity": similarity})

    if not candidates:
        return None

    with_similarity = [c for c in candidates if c["similarity"] is not None]
    if with_similarity:
        return min(with_similarity, key=lambda c: c["similarity"])

    return min(candidates, key=lambda c: c["distance_meters"])


if __name__ == "__main__":
    print("This module is meant to be imported and called with real complaint data.")
    print("Example: find_recurrence(new_complaint, resolved_complaints_from_db)")
