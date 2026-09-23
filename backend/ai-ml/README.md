# CiviSense — ai-ml module

Standalone Python modules for the AI features that sit alongside YOLO detection.
Each one is independent, testable on its own, and honest about failure —
none of them invent a result when they can't produce a real one.

## Files

| File | What it does | Depends on |
|---|---|---|
| `image_quality.py` | Blur/darkness check on a photo before it reaches YOLO | opencv-python-headless |
| `description_generator.py` | Builds a plain-English description from a detection dict | (none — pure Python) |
| `duplicate_detection.py` | Flags a new complaint as a likely duplicate of an existing OPEN complaint | Pillow, ImageHash |
| `recurrence_detection.py` | Flags a new complaint as a likely recurrence of a RESOLVED complaint at the same spot | duplicate_detection.py |
| `voice_to_text.py` | Transcribes a voice note using Whisper | openai-whisper |

## Setup

```bash
cd ai-ml
pip install -r requirements.txt --break-system-packages
```

(`openai-whisper` also needs `ffmpeg` installed on your system: `brew install ffmpeg` on Mac.)

## How these plug into your backend

None of these files run a server themselves — they're plain functions your
FastAPI backend imports and calls during complaint submission. Rough flow
for `POST /complaints`:

```python
from ai_ml.image_quality import check_images
from ai_ml.description_generator import generate_description
from ai_ml.duplicate_detection import find_duplicate
from ai_ml.recurrence_detection import find_recurrence
from ai_ml.voice_to_text import transcribe_voice_note

# 1. Quality check every uploaded photo — reject before running YOLO
quality_results = check_images(saved_image_paths)
if any(r["status"] != "ok" for r in quality_results):
    return {"status": "rejected", "reason": "photo quality", "details": quality_results}

# 2. Run YOLO detection (your existing yolo_detector.py)
detections = run_yolo_detection(saved_image_paths)

# 3. Auto-generate a description if the citizen didn't type one
if not description:
    description = generate_description(detections[0]) if detections else "No description provided."

# 4. Check for duplicates against OPEN complaints from the database
open_complaints = db.get_complaints(status_not="resolved")
duplicate = find_duplicate(new_complaint, open_complaints)
if duplicate:
    # link this submission to the existing complaint instead of creating a new one
    ...

# 5. Check for recurrence against RESOLVED complaints from the database
resolved_complaints = db.get_complaints(status="resolved")
recurrence = find_recurrence(new_complaint, resolved_complaints)
if recurrence:
    # flag for admin review
    ...

# 6. If a voice note was uploaded, transcribe it
if voice_note_path:
    transcription = transcribe_voice_note(voice_note_path)
```

## What's intentionally NOT here yet

- **Trend/heatmap analytics** — needs real accumulated complaint data to be
  meaningful, and lives better as a database query + chart in the admin
  dashboard frontend, not a standalone AI module. Once complaints exist in
  the database, this is a `GROUP BY` query + a chart component.
- **Explainability (SHAP)** — deliberately skipped per your instructions;
  revisit once the priority model is trained on real data.

## Honesty notes (read before wiring these in)

- Duplicate/recurrence thresholds (`radius_meters`, image hash thresholds)
  are reasonable starting points, not tuned on your real data yet.
- `description_generator.py` never states a size or confidence that isn't
  in the detection dict it's given.
- `voice_to_text.py` returns a clear `"status": "error"` on failure rather
  than pretending a transcription happened.
