"""Score existing complaints with the trained model.

Run from the backend directory (venv active):
    python scripts/score_existing_complaints.py
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal  # noqa: E402
from app.models import complaint as _c  # noqa: E402,F401
from app.models import user as _u  # noqa: E402,F401
from app.models.complaint import Complaint  # noqa: E402
from app.services import ml  # noqa: E402


def main():
    session = SessionLocal()
    done = skipped = 0
    try:
        for c in session.query(Complaint).all():
            category = (c.issue_type or "").strip() or (c.reported_category or "").strip()
            result = ml.predict(c.description, category)
            if result is None:
                skipped += 1
                continue
            c.severity_score = float(result["severity"])
            c.priority_score = float(result["priority"])
            c.ai_status = "processed"
            done += 1
        session.commit()
    finally:
        session.close()
    print(f"Scored {done} complaints, skipped {skipped}.")


if __name__ == "__main__":
    main()