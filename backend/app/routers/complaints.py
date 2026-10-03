from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import String, cast, func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.complaint import Complaint, ComplaintPhoto, ComplaintStatus
from app.models.user import User
from app.schemas.complaint import ComplaintOut, ComplaintPhotoOut
from app.services.storage import save_photo, save_voice_note, to_public_path
from app.services import ml

router = APIRouter(prefix="/complaints", tags=["complaints"])


class CategoryTrendPoint(BaseModel):
    period: str
    count: int


class CategoryStats(BaseModel):
    category: str
    count: int
    percentage: float
    trend: list[CategoryTrendPoint]


class CategoryStatsResponse(BaseModel):
    period_days: int
    interval: str
    total: int
    categories: list[CategoryStats]


def _parse_created_at(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _bucket_start(value: datetime, interval: str) -> datetime:
    day = value.date()
    if interval == "week":
        day -= timedelta(days=day.weekday())
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)


@router.get("/stats/by-category", response_model=CategoryStatsResponse)
def stats_by_category(
    days: int = Query(default=30, ge=1),
    interval: Literal["day", "week"] = Query(default="week"),
    db: Session = Depends(get_db),
):
    """Return category counts and a complete daily or weekly trend."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    category_expr = func.coalesce(
        func.nullif(func.trim(Complaint.issue_type), ""),
        func.nullif(func.trim(Complaint.reported_category), ""),
        "Uncategorized",
    )

    # Cast the timestamp to text so SQLite's DateTime result processor cannot
    # fail on legacy string values; parse each value defensively below.
    rows = db.query(
        category_expr.label("category"),
        cast(Complaint.created_at, String).label("created_at"),
    ).all()

    first_bucket = _bucket_start(cutoff, interval)
    last_bucket = _bucket_start(now, interval)
    periods = []
    cursor = first_bucket
    step = timedelta(days=1 if interval == "day" else 7)
    while cursor <= last_bucket:
        periods.append(cursor.date().isoformat())
        cursor += step

    category_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        created_at = _parse_created_at(row.created_at)
        if created_at is None or created_at < cutoff or created_at > now:
            continue
        category = row.category or "Uncategorized"
        period = _bucket_start(created_at, interval).date().isoformat()
        category_counts.setdefault(category, {}).setdefault(period, 0)
        category_counts[category][period] += 1

    total = sum(sum(counts.values()) for counts in category_counts.values())
    categories = [
        CategoryStats(
            category=category,
            count=sum(counts.values()),
            percentage=round(sum(counts.values()) * 100 / total, 1) if total else 0.0,
            trend=[CategoryTrendPoint(period=period, count=counts.get(period, 0)) for period in periods],
        )
        for category, counts in category_counts.items()
    ]
    categories.sort(key=lambda item: (-item.count, item.category))

    return CategoryStatsResponse(
        period_days=days,
        interval=interval,
        total=total,
        categories=categories,
    )


def _to_out(c: Complaint) -> ComplaintOut:
    photo_urls = [ComplaintPhotoOut(id=p.id, url=to_public_path(p.file_path)) for p in c.photos]
    return ComplaintOut(
        id=c.id,
        description=c.description,
        status=c.status.value if hasattr(c.status, "value") else c.status,
        lat=c.lat,
        lng=c.lng,
        address=c.address,
        reported_category=c.reported_category,
        reported_severity=c.reported_severity,
        photo_url=photo_urls[0].url if photo_urls else None,
        photos=photo_urls,
        voice_note_url=to_public_path(c.voice_note_path) if c.voice_note_path else None,
        issue_type=c.issue_type,
        severity_score=c.severity_score,
        priority_score=c.priority_score,
        ai_status=c.ai_status,
        created_at=c.created_at,
    )


@router.post("", response_model=ComplaintOut, status_code=201)
async def create_complaint(
    description: str = Form(...),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
    reported_category: Optional[str] = Form(None),
    reported_severity: Optional[str] = Form(None),
    photos: list[UploadFile] = File(default=[]),
    voice_note: Optional[UploadFile] = File(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not description or not description.strip():
        raise HTTPException(status_code=400, detail="Description is required")

    complaint = Complaint(
        user_id=current_user.id,
        description=description.strip(),
        lat=lat,
        lng=lng,
        address=address,
        reported_category=reported_category,
        reported_severity=reported_severity,
    )

    if voice_note is not None and voice_note.filename:
        complaint.voice_note_path = await save_voice_note(voice_note)

    db.add(complaint)
    db.flush()  # get complaint.id before attaching photos

    for photo in photos:
        if not photo.filename:
            continue
        path = await save_photo(photo)
        db.add(ComplaintPhoto(complaint_id=complaint.id, file_path=path))

    db.commit()
    db.refresh(complaint)

        # Score with the trained model. If it is unavailable, ai_status stays
    # "unavailable" rather than a fabricated value.
    prediction = ml.predict(complaint.description, complaint.reported_category)
    if prediction is not None:
        complaint.severity_score = float(prediction["severity"])
        complaint.priority_score = float(prediction["priority"])
        complaint.ai_status = "processed"
        db.commit()
        db.refresh(complaint)

    return _to_out(complaint)


@router.get("/mine", response_model=list[ComplaintOut])
def list_my_complaints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    complaints = (
        db.query(Complaint)
        .filter(Complaint.user_id == current_user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return [_to_out(c) for c in complaints]


@router.get("", response_model=list[ComplaintOut])
def list_complaints(
    status: Optional[str] = None,
    issue_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)
    if status:
        query = query.filter(Complaint.status == status)
    if issue_type:
        query = query.filter(Complaint.issue_type == issue_type)
    complaints = query.order_by(Complaint.created_at.desc()).all()
    return [_to_out(c) for c in complaints]


class StatusUpdate(BaseModel):
    status: ComplaintStatus


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(complaint_id: str, body: StatusUpdate, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    complaint.status = body.status
    db.commit()
    db.refresh(complaint)
    return _to_out(complaint)


@router.get("/stats/summary")
def stats_summary(db: Session = Depends(get_db)):
    """Real counts from the database — no fabricated dashboard numbers."""
    total = db.query(Complaint).count()
    by_status = {}
    for s in ComplaintStatus:
        by_status[s.value] = db.query(Complaint).filter(Complaint.status == s).count()
    return {"total": total, "by_status": by_status}


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return _to_out(complaint)



@router.get("/{complaint_id}/explanation")
def get_complaint_explanation(complaint_id: str, db: Session = Depends(get_db)):
    """Severity/priority prediction with SHAP reasons for one complaint."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    category = (complaint.issue_type or "").strip() or (complaint.reported_category or "").strip()
    result = ml.explain(complaint.description, category)
    if result is None:
        raise HTTPException(status_code=503, detail="Severity/priority model is not available")
    return result