import os
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

from app.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/mpeg", "audio/mp4", "audio/wav", "audio/ogg"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


def _ensure_dirs() -> tuple[Path, Path]:
    base = Path(settings.upload_dir)
    photos_dir = base / "photos"
    voice_dir = base / "voice"
    photos_dir.mkdir(parents=True, exist_ok=True)
    voice_dir.mkdir(parents=True, exist_ok=True)
    return photos_dir, voice_dir


async def _save(file: UploadFile, dest_dir: Path, allowed_types: set[str]) -> str:
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}' for {file.filename}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"{file.filename} is larger than 15MB")

    ext = os.path.splitext(file.filename or "")[1] or ""
    name = f"{uuid.uuid4().hex}{ext}"
    path = dest_dir / name
    with open(path, "wb") as f:
        f.write(contents)

    return str(path)


async def save_photo(file: UploadFile) -> str:
    photos_dir, _ = _ensure_dirs()
    return await _save(file, photos_dir, ALLOWED_IMAGE_TYPES)


async def save_voice_note(file: UploadFile) -> str:
    _, voice_dir = _ensure_dirs()
    return await _save(file, voice_dir, ALLOWED_AUDIO_TYPES)


def to_public_path(disk_path: str) -> str:
    """Convert an absolute/relative disk path under UPLOAD_DIR into the
    '/uploads/...' URL path that main.py mounts as static files."""
    rel = os.path.relpath(disk_path, settings.upload_dir)
    return f"/uploads/{rel.replace(os.sep, '/')}"
