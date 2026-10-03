from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.complaint import Complaint, ComplaintPhoto, ComplaintStatus
from app.models.user import User
from app.schemas.complaint import ComplaintOut, ComplaintPhotoOut
from app.services.storage import save_photo, save_voice_note, to_public_path

router = APIRouter(prefix="/complaints", tags=["complaints"])

# A complaint still "submitted" after this many days is flagged as escalated.
ESCALATION_DAYS = 0


def _status_value(c: Complaint) -> str:
    return c.status.value if hasattr(c.status, "value") else c.status


def _is_escalated(c: Complaint) -> bool:
    """Plain date math, no AI: unattended for more than ESCALATION_DAYS."""
    if _status_value(c) != "submitted" or c.created_at is None:
        return False
    return datetime.utcnow() - c.created_at > timedelta(days=ESCALATION_DAYS)


def _to_out(c: Complaint) -> ComplaintOut:
    photo_urls = [ComplaintPhotoOut(id=p.id, url=to_public_path(p.file_path)) for p in c.photos]
    return ComplaintOut(
        id=c.id,
        description=c.description,
        status=_status_value(c),
        lat=c.lat,
        lng=c.lng,
        address=c.address,
        reported_category=c.reported_category,
        reported_severity=c.reported_severity,
        photo_url=photo_urls[0].url if photo_urls else None,
        photos=photo_urls,
        voice_note_url=to_public_path(c.voice_note_path) if c.voice_note_path else None,
        after_photo_url=to_public_path(c.after_photo_path) if c.after_photo_path else None,
        issue_type=c.issue_type,
        severity_score=c.severity_score,
        priority_score=c.priority_score,
        ai_status=c.ai_status,
        escalated=_is_escalated(c),
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

    # NOTE: no severity/priority is computed here. The ai-ml pipeline is a
    # separate, honest step. Until it runs against this complaint,
    # ai_status stays "unavailable" rather than a fabricated score.

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


@router.post("/{complaint_id}/resolve", response_model=ComplaintOut)
async def resolve_complaint(
    complaint_id: str,
    after_photo: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
):
    """Mark resolved. An 'after' photo is optional."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if after_photo is not None and after_photo.filename:
        complaint.after_photo_path = await save_photo(after_photo)

    complaint.status = ComplaintStatus("resolved")
    db.commit()
    db.refresh(complaint)
    return _to_out(complaint)


# Must stay above "/{complaint_id}" so "stats" isn't read as an id.
@router.get("/stats/summary")
def stats_summary(db: Session = Depends(get_db)):
    """Real counts from the database. No fabricated dashboard numbers."""
    total = db.query(Complaint).count()
    by_status = {
        s.value: db.query(Complaint).filter(Complaint.status == s).count()
        for s in ComplaintStatus
    }
    # Only complaints where detection actually produced an issue_type are
    # counted; the rest are left out instead of being put in a fake bucket.
    rows = (
        db.query(Complaint.issue_type, func.count(Complaint.id))
        .filter(Complaint.issue_type.isnot(None))
        .group_by(Complaint.issue_type)
        .all()
    )
    return {
        "total": total,
        "by_status": by_status,
        "by_category": {category: count for category, count in rows},
    }


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return _to_out(complaint)