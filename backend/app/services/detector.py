from io import BytesIO
from pathlib import Path

from app.services.verification import _find_file

# backend/app/services/detector.py -> parents[3] is the pdl-1 folder
MODEL_PATH = Path(__file__).resolve().parents[3] / "ai-ml" / "models" / "best.pt"

# Below this confidence we do NOT label the complaint (issue_type stays null).
CONF_THRESHOLD = 0.5

_model = None


def _get_model():
    global _model
    if _model is None:
        from ultralytics import YOLO
        _model = YOLO(str(MODEL_PATH))
    return _model


def _best_detection(source):
    """Return (class_name, confidence) of the most confident box at or above
    CONF_THRESHOLD, else None."""
    model = _get_model()
    result = model(source, verbose=False)[0]
    best = None
    for box in result.boxes:
        conf = float(box.conf)
        if conf >= CONF_THRESHOLD and (best is None or conf > best[1]):
            best = (model.names[int(box.cls)], conf)
    return best


def detect_issue(stored_photo_path: str):
    """Returns the top class name if confidence >= CONF_THRESHOLD,
    otherwise None. Any failure also returns None (no guessing)."""
    try:
        photo = _find_file(stored_photo_path)
        if photo is None or not MODEL_PATH.is_file():
            return None
        best = _best_detection(str(photo))
        return best[0] if best else None
    except Exception:
        return None


def detect_issue_in_bytes(data: bytes):
    """Same check for an uploaded image (used for the 'after' photo).
    Returns (class_name, confidence) or None. Any failure returns None."""
    try:
        if not MODEL_PATH.is_file():
            return None
        from PIL import Image
        with Image.open(BytesIO(data)) as img:
            return _best_detection(img.convert("RGB"))
    except Exception:
        return None