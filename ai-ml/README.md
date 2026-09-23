# CiviSense — AI/ML module

Detects road issues (pothole, speed_breaker, unpaved_road) from citizen-submitted
photos. This module is independent of `backend/` — the backend calls into it
once a trained model exists; it does not fabricate results in the meantime.

## No-fake-AI rule (applies to everything built in here)

- If no trained model file exists on disk, any inference function must return
  `{"status": "unavailable", "reason": "..."}` — never a made-up score.
- Severity / priority / SHAP explanations must say "unavailable" rather than
  invent numbers when the underlying model or data doesn't exist yet.

## Folder layout

```
ai-ml/
  database/
    data.yaml              <- class names + split paths (edit paths if needed)
    images/{train,val,test}/
    labels/{train,val,test}/   <- YOLO-format .txt, one per image
  models/                   <- trained weights land here (best.pt, etc.) — gitignored
  scripts/
    audit_dataset.py        <- run this FIRST, before any training
```

## Step 1 — put your real dataset in place

Copy your (already deduplicated) images and labels into:

```
database/images/train/  database/images/val/  database/images/test/
database/labels/train/  database/labels/val/  database/labels/test/
```

Each image needs a same-named `.txt` label file in the matching `labels/<split>/`
folder (standard YOLO format: `class_id x_center y_center width height`, all
normalized 0–1).

## Step 2 — run the audit (this is where we stop and wait)

```bash
cd ai-ml
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 scripts/audit_dataset.py
```

This checks, per split: missing labels, empty labels, invalid class indices,
corrupt images, and real per-class box counts. It does **not** train anything
and does **not** tell you the dataset is "good enough" — only whether it's
structurally sound. Read the verdict at the bottom.

**Do not move on to YOLO training until this comes back clean** (or you've
consciously decided to proceed despite specific gaps, e.g. collecting more
`speed_breaker` examples first).

## Step 3 (next, once audit is clean)

Training script, severity/priority/SHAP modules — built after you share the
audit output, since what those need depends on what's actually in the data.
