import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class ComplaintStatus(str, enum.Enum):
    submitted = "submitted"
    in_progress = "in_progress"
    resolved = "resolved"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String, primary_key=True, default=gen_id)
    description = Column(Text, nullable=False)

    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    address = Column(String, nullable=True)

    voice_note_path = Column(String, nullable=True)

    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.submitted, nullable=False)

    # Populated by the ai-ml pipeline once it runs against this complaint.
    # Left null (not a fabricated value) until a real model has scored it —
    # see ai-ml/ for the "no fake AI output" rule this follows.
    issue_type = Column(String, nullable=True)        # e.g. "pothole", "speed_breaker", "unpaved_road"
    severity_score = Column(Float, nullable=True)
    priority_score = Column(Float, nullable=True)
    ai_status = Column(String, default="unavailable", nullable=False)  # "unavailable" | "processed"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    photos = relationship("ComplaintPhoto", back_populates="complaint", cascade="all, delete-orphan")


class ComplaintPhoto(Base):
    __tablename__ = "complaint_photos"

    id = Column(String, primary_key=True, default=gen_id)
    complaint_id = Column(String, ForeignKey("complaints.id"), nullable=False)
    file_path = Column(String, nullable=False)

    complaint = relationship("Complaint", back_populates="photos")
