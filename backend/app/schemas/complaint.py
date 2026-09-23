from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ComplaintPhotoOut(BaseModel):
    id: str
    url: str

    model_config = ConfigDict(from_attributes=True)


class ComplaintOut(BaseModel):
    id: str
    description: str
    status: str

    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None

    photo_url: Optional[str] = None  # first photo, for the list-view thumbnail
    photos: list[ComplaintPhotoOut] = []
    voice_note_url: Optional[str] = None

    issue_type: Optional[str] = None
    severity_score: Optional[float] = None
    priority_score: Optional[float] = None
    ai_status: str = "unavailable"

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
