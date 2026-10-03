from pathlib import Path
from io import BytesIO

from PIL import Image

from app.config import settings

HASH_SIZE = 8
# Out of 64 bits. 0 means identical; small numbers mean nearly the same picture.
SAME_PHOTO_MAX_DISTANCE = 6


def _dhash(img: Image.Image) -> int:
    img = img.convert("L").resize((HASH_SIZE + 1, HASH_SIZE), Image.LANCZOS)
    px = list(img.getdata())
    bits = 0
    for row in range(HASH_SIZE):
        for col in range(HASH_SIZE):
            left = px[row * (HASH_SIZE + 1) + col]
            right = px[row * (HASH_SIZE + 1) + col + 1]
            bits = (bits << 1) | (1 if left > right else 0)
    return bits


def _find_file(stored_path: str):
    """The stored path format varies, so try a few likely places."""
    name = Path(stored_path).name
    candidates = [
        Path(stored_path),
        Path.cwd() / stored_path.lstrip("/"),
        Path(settings.upload_dir) / "photos" / name,
        Path(settings.upload_dir) / name,
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def compare_with_before(before_stored_path: str, after_bytes: bytes):
    """Returns {"distance": int, "too_similar": bool}, or None if the
    comparison could not be made (we never guess in that case)."""
    try:
        before_file = _find_file(before_stored_path)
        if before_file is None:
            return None
        with Image.open(before_file) as before_img:
            before_hash = _dhash(before_img)
        with Image.open(BytesIO(after_bytes)) as after_img:
            after_hash = _dhash(after_img)
    except Exception:
        return None
    distance = bin(before_hash ^ after_hash).count("1")
    return {"distance": distance, "too_similar": distance <= SAME_PHOTO_MAX_DISTANCE}