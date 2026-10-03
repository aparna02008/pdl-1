"""Add 8 low-severity demo complaints (severity 1, priority 1) and append their labels.

Run ONCE from the backend directory:
    python scripts/add_low_severity_demo.py
"""
import csv
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal  # noqa: E402
from app.models import complaint as _c  # noqa: E402,F401
from app.models import user as _u  # noqa: E402,F401
from app.models.complaint import Complaint  # noqa: E402
from app.models.user import User  # noqa: E402
from seed_demo_complaints import CHENNAI_AREAS, ISSUE_DETAILS, STATUSES, STREETS  # noqa: E402

# (category, template index): all severity 1 templates
SPECS = [
    ("garbage", 1), ("garbage", 1),          # overflowing bin
    ("streetlight", 2), ("streetlight", 2),  # flickering lamp
    ("water_leak", 0), ("water_leak", 0),    # clean-water leak
    ("drainage", 2), ("drainage", 2),        # clogged drain
]
# No school / health centre / junction / main road crossing -> no priority +1
LANDMARKS_OK = [
    "the bus stop", "the market entrance", "the local park",
    "the water tank", "the temple", "the railway station approach",
]


def append_rows(path, rows):
    p = Path(path)
    if not p.exists():
        print(f"skip (not found): {path}")
        return
    needs_newline = not p.read_bytes().endswith(b"\n")
    with open(p, "a", newline="", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        csv.writer(f).writerows(rows)
    print(f"appended {len(rows)} rows to {path}")


def main():
    rng = random.Random()
    now = datetime.now(timezone.utc)
    session = SessionLocal()
    v1_rows, final_rows = [], []
    try:
        user = session.query(User).filter(User.email == "demo@civisense.local").first()
        if user is None:
            raise SystemExit("demo user not found, run seed_demo_complaints.py once first")

        for category, idx in SPECS:
            area, lat0, lng0 = rng.choice(CHENNAI_AREAS)
            landmark = rng.choice(LANDMARKS_OK)
            desc = "[DEMO] " + ISSUE_DETAILS[category][idx].format(landmark=landmark)
            created = now - timedelta(seconds=rng.randint(0, 30 * 24 * 60 * 60))
            sev_reported = rng.choice(["low", "medium", "high", "critical"])
            address = f"{rng.choice(STREETS)}, {area}, Chennai"
            lat = round(lat0 + rng.uniform(-0.009, 0.009), 6)
            lng = round(lng0 + rng.uniform(-0.009, 0.009), 6)

            c = Complaint(
                description=desc, user_id=user.id, reported_category=category,
                reported_severity=sev_reported, address=address, lat=lat, lng=lng,
                status=rng.choice(STATUSES), created_at=created, ai_status="unavailable",
            )
            session.add(c)
            session.flush()  # assigns c.id
            ts = created.strftime("%Y-%m-%d %H:%M:%S.%f")
            v1_rows.append([c.id, category, category, sev_reported, desc, address, lat, lng, ts, 1, 1])
            final_rows.append([c.id, category, 1, 1])
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    append_rows("labels_v1.csv", v1_rows)
    append_rows("labels_final.csv", final_rows)
    print("Done. Do NOT run this script again.")


if __name__ == "__main__":
    main()