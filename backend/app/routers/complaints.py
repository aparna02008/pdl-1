import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "ai-ml"))

from image_quality import check_images
from description_generator import generate_description
from duplicate_detection import find_duplicate
from recurrence_detection import find_recurrence
from voice_to_text import transcribe_voice_note

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.complaint import Complaint, ComplaintPhoto, ComplaintStatus
from app.schemas.complaint import ComplaintOut, ComplaintPhotoOut
from app.services.storage import save_photo, save_voice_note, to_public_path

router = APIRouter(prefix="/complaints", tags=["complaints"])


def _to_out(c: Complaint) -> ComplaintOut:
    photo_urls = [ComplaintPhotoOut(id=p.id, url=to_public_path(p.file_path)) for p in c.photos]
    return ComplaintOut(
        id=c.id,
        description=c.description,
        status=c.status.value if hasattr(c.status, "value") else c.status,
        lat=c.lat,
        lng=c.lng,
        address=c.address,
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
    description: Optional[str] = Form(None),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
    photos: list[UploadFile] = File(default=[]),
    voice_note: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
):
    if not photos or all(not p.filename for p in photos):
        raise HTTPException(status_code=400, detail="At least one photo is required")

    # 1. Save photos to disk first so quality check can run on real files
    saved_photo_paths = []
    for photo in photos:
        if not photo.filename:
            continue
        path = await save_photo(photo)
        saved_photo_paths.append(path)

    # 2. Image quality check — reject unusable photos before anything else
    quality_results = check_images(saved_photo_paths)
    bad_photos = [r for r in quality_results if r["status"] != "ok"]
    if bad_photos:
        raise HTTPException(
            status_code=400,
            detail=f"Photo quality issue: {bad_photos[0]['status']}. Please retake the photo.",
        )

    # 3. Duplicate check — against currently OPEN complaints, only if we have a location
    duplicate_match = None
    if lat is not None and lng is not None:
        open_complaints = (
            db.query(Complaint)
            .filter(Complaint.status != ComplaintStatus.resolved)
            .all()
        )
        existing_for_check = [
            {
                "id": c.id,
                "latitude": c.lat,
                "longitude": c.lng,
                "image_path": c.photos[0].file_path if c.photos else None,
                "category": c.issue_type,
                "status": c.status.value if hasattr(c.status, "value") else c.status,
            }
            for c in open_complaints
            if c.lat is not None and c.lng is not None and c.photos
        ]
        duplicate_match = find_duplicate(
            {"latitude": lat, "longitude": lng, "image_path": saved_photo_paths[0], "category": None},
            existing_for_check,
        )

    # 4. Recurrence check — against RESOLVED complaints, only if not already a duplicate
    recurrence_match = None
    if lat is not None and lng is not None and duplicate_match is None:
        resolved_complaints = (
            db.query(Complaint)
            .filter(Complaint.status == ComplaintStatus.resolved)
            .all()
        )
        resolved_for_check = [
            {
                "id": c.id,
                "latitude": c.lat,
                "longitude": c.lng,
                "image_path": c.photos[0].file_path if c.photos else None,
                "category": c.issue_type,
            }
            for c in resolved_complaints
            if c.lat is not None and c.lng is not None and c.photos
        ]
        recurrence_match = find_recurrence(
            {"latitude": lat, "longitude": lng, "image_path": saved_photo_paths[0], "category": None},
            resolved_for_check,
        )

    # 5. Voice note — save it, then transcribe with Whisper if present
    voice_transcription = None
    voice_note_path = None
    if voice_note is not None and voice_note.filename:
        voice_note_path = await save_voice_note(voice_note)
        transcription_result = transcribe_voice_note(voice_note_path)
        if transcription_result["status"] == "ok" and transcription_result["text"]:
            voice_transcription = transcription_result["text"]

    # 6. Description — use what the citizen typed; if empty, fall back to the
    #    voice transcription; if that's also missing, use a plain placeholder.
    #    (Auto-description from YOLO detection happens once the detection
    #    pipeline runs on this complaint — not yet wired in, per ai-ml/README.md.)
    if description and description.strip():
        final_description = description.strip()
    elif voice_transcription:
        final_description = voice_transcription
    else:
        final_description = "No description provided."

    complaint = Complaint(
        description=final_description,
        lat=lat,
        lng=lng,
        address=address,
    )

    if voice_note_path:
        complaint.voice_note_path = voice_note_path

    db.add(complaint)
    db.flush()

    for path in saved_photo_paths:
        db.add(ComplaintPhoto(complaint_id=complaint.id, file_path=path))

    db.commit()
    db.refresh(complaint)

    result = _to_out(complaint)
    result_dict = result.model_dump()

    if duplicate_match:
        result_dict["duplicate_warning"] = {
            "matched_complaint_id": duplicate_match["id"],
            "distance_meters": duplicate_match["distance_meters"],
        }
    if recurrence_match:
        result_dict["recurrence_warning"] = {
            "previously_resolved_complaint_id": recurrence_match["id"],
            "distance_meters": recurrence_match["distance_meters"],
        }
    if voice_transcription:
        result_dict["voice_transcription"] = voice_transcription

    return result_dict


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
