"""
Converts a classification-style folder (a Roboflow "Folder" export, or any
folder that's just whole photos with no bounding boxes) into YOLO-format
labels, by treating the whole image as one box for the given class.

HONEST LIMITATION: this is a weak label. Real bounding boxes point at the
exact object; a full-frame box just says "this class appears somewhere in
this photo." It's usable — much better than dropping the data — but it will
be less precise than the properly-boxed classes (pothole, garbage, etc.).
Document this clearly in any report on the trained model.

Usage:
    python3 folder_to_yolo.py --src "path/to/Illegal Parking Issues" --class-id 0 --out flat_out

--class-id is a PLACEHOLDER (use 0) — remap_and_merge.py remaps it to the
real unified class number in the next step.
"""

import argparse
import shutil
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# Box covers most of the frame but not literally 100%, since a full 1.0x1.0
# box sometimes gets clipped/rejected by training pipelines.
BOX = (0.5, 0.5, 0.96, 0.96)  # xc, yc, w, h


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="Folder of whole-image photos (one category)")
    parser.add_argument("--class-id", type=int, default=0, help="Placeholder class id to write")
    parser.add_argument("--out", required=True, help="Output flat folder (created)")
    args = parser.parse_args()

    src = Path(args.src).expanduser()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    images = [p for p in src.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    if not images:
        print(f"ERROR: no images found under {src}")
        return

    xc, yc, w, h = BOX
    for img_path in images:
        dest_name = img_path.stem.replace(" ", "_")
        shutil.copy2(img_path, out / f"{dest_name}{img_path.suffix}")
        (out / f"{dest_name}.txt").write_text(f"{args.class_id} {xc} {yc} {w} {h}\n")

    print(f"Converted {len(images)} images (full-frame box, class {args.class_id})")
    print(f"Output written to: {out}")
    print("NOTE: these are whole-image approximate boxes, not precise object boxes.")


if __name__ == "__main__":
    main()
