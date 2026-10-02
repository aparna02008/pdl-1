"""Insert clearly marked demo complaints into the configured SQLite database.

Run from the backend directory so the app's default ``./civisense.db`` and
``.env`` settings are used:

    python scripts/seed_demo_complaints.py [N]
"""

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.auth import hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import complaint as _complaint_models  # noqa: E402,F401
from app.models import user as _user_models  # noqa: E402,F401
from app.models.complaint import Complaint, ComplaintStatus  # noqa: E402
from app.models.user import User  # noqa: E402


ISSUE_DETAILS = {
    "pothole": [
        "A deep pothole has opened up near {landmark}; two-wheelers are swerving into traffic to avoid it.",
        "The road surface is broken and uneven outside {landmark}, especially dangerous after dark.",
        "Several potholes have formed along this stretch near {landmark} and collect water after rain.",
    ],
    "garbage": [
        "Household waste has been piling up near {landmark} for several days and is attracting stray animals.",
        "The public bin beside {landmark} is overflowing onto the footpath.",
        "A large garbage heap near {landmark} is blocking part of the road and causing a bad smell.",
    ],
    "streetlight": [
        "The streetlight near {landmark} has not been working, leaving this crossing very dark at night.",
        "Two lights along the road near {landmark} are out and pedestrians are difficult to see after sunset.",
        "The lamp post outside {landmark} flickers and then goes dark most evenings.",
    ],
    "water_leak": [
        "Clean water is leaking steadily from a pipe near {landmark} and running across the road.",
        "A water pipe appears to have burst beside {landmark}; water has been flowing since this morning.",
        "There is a persistent leak near {landmark}, making the road slippery for traffic.",
    ],
    "drainage": [
        "The storm drain near {landmark} is blocked and rainwater is backing up onto the street.",
        "An open drain beside {landmark} is overflowing and creating a hazard for pedestrians.",
        "Water is stagnating near {landmark} because the roadside drain appears clogged.",
    ],
    "fallen_tree": [
        "A fallen tree branch is obstructing the road near {landmark} and narrowing the carriageway.",
        "A tree has fallen across part of the footpath near {landmark}; pedestrians have to walk in the road.",
        "Large branches came down near {landmark} and are blocking one side of the street.",
    ],
}

CHENNAI_AREAS = [
    ("T. Nagar", 13.0418, 80.2337),
    ("Adyar", 13.0067, 80.2570),
    ("Velachery", 12.9750, 80.2210),
    ("Anna Nagar", 13.0850, 80.2101),
    ("Mylapore", 13.0368, 80.2676),
    ("Perambur", 13.1167, 80.2333),
    ("Guindy", 13.0067, 80.2206),
    ("Royapettah", 13.0551, 80.2632),
    ("Kodambakkam", 13.0524, 80.2210),
    ("Thiruvanmiyur", 12.9830, 80.2594),
    ("Nungambakkam", 13.0569, 80.2425),
    ("Ashok Nagar", 13.0358, 80.2121),
    ("Tambaram", 12.9249, 80.1000),
    ("Porur", 13.0358, 80.1561),
    ("Triplicane", 13.0588, 80.2756),
]

LANDMARKS = [
    "the bus stop", "the market entrance", "the school gate", "the local park",
    "the junction", "the community health centre", "the main road crossing",
    "the railway station approach", "the temple", "the water tank",
]
STREETS = [
    "Gandhi Road", "Lake View Road", "Station Road", "Market Street",
    "School Road", "Cross Street", "Beach Road", "Temple Street",
]
STATUSES = list(ComplaintStatus)


def make_demo_complaint(rng: random.Random, now: datetime, user_id: str) -> Complaint:
    category = rng.choice(list(ISSUE_DETAILS))
    area, center_lat, center_lng = rng.choice(CHENNAI_AREAS)
    landmark = rng.choice(LANDMARKS)
    street = rng.choice(STREETS)
    description = rng.choice(ISSUE_DETAILS[category]).format(landmark=landmark)

    return Complaint(
        description=f"[DEMO] {description}",
        user_id=user_id,
        reported_category=category,
        reported_severity=rng.choice(["low", "medium", "high", "critical"]),
        address=f"{street}, {area}, Chennai",
        lat=round(center_lat + rng.uniform(-0.009, 0.009), 6),
        lng=round(center_lng + rng.uniform(-0.009, 0.009), 6),
        status=rng.choice(STATUSES),
        created_at=now - timedelta(seconds=rng.randint(0, 60 * 24 * 60 * 60)),
        # Keep AI-derived fields unset; these are demo reports, not model output.
        ai_status="unavailable",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo complaints into civisense.db")
    parser.add_argument("n", nargs="?", type=int, default=80, help="number of complaints to add (default: 80)")
    args = parser.parse_args()
    if args.n < 0:
        parser.error("N must be zero or greater")

    rng = random.Random()
    now = datetime.now(timezone.utc)
    session = SessionLocal()
    try:
        demo_user = session.query(User).filter(User.email == "demo@civisense.local").first()
        if demo_user is None:
            demo_user = User(
                email="demo@civisense.local",
                name="CiviSense Demo",
                hashed_password=hash_password("civisense-demo-password"),
            )
            session.add(demo_user)
            session.flush()

        session.add_all(make_demo_complaint(rng, now, demo_user.id) for _ in range(args.n))
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print(f"Inserted {args.n} demo complaint(s).")


if __name__ == "__main__":
    main()
