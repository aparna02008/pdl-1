"""
Converts a folder of binary segmentation masks (pixel values 0/1, like the
waterlogging dataset) into YOLO-format bounding box .txt files, so they can
go through the normal remap_and_merge.py pipeline afterwards.

Why: our training pipeline (and remap_and_merge.py) expects YOLO text boxes,
not pixel masks. This is a one-time, honest conversion — it finds the actual
connected white regions in each mask and draws a box around each one. It does
NOT invent boxes for masks that are all-zero (no flooding visible) — those
images are skipped, not falsely labeled.

Usage:
    python3 mask_to_yolo.py --images images/ --masks labels/ --out flat_out/ --class-id 0

--class-id is a PLACEHOLDER class number (use 0) — remap_and_merge.py will
remap it to the real unified class (waterlogging = 4) in the next step.

Output: flat_out/ containing <name>.jpg (copied) + <name>.txt (YOLO boxes),
ready to feed into remap_and_merge.py with --src flat_out --map 0:4
"""

import argparse
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def mask_to_boxes(mask: np.ndarray) -> list[tuple[float, float, float, float]]:
    """Returns list of (x_center, y_center, width, height), all normalized 0-1,
    one per connected white region in the mask. Empty list if mask is all zero."""
    binary = (mask > 0).astype(np.uint8)
    if binary.sum() == 0:
        return []

    labeled, num_features = ndimage.label(binary)
    h, w = mask.shape[:2]
    boxes = []

    for i in range(1, num_features + 1):
        ys, xs = np.where(labeled == i)
        if len(xs) < 20:  # skip tiny noise specks (fewer than 20 pixels)
            continue
        x1, x2 = xs.min(), xs.max()
        y1, y2 = ys.min(), ys.max()

        xc = (x1 + x2) / 2 / w
        yc = (y1 + y2) / 2 / h
        bw = (x2 - x1) / w
        bh = (y2 - y1) / h
        boxes.append((xc, yc, bw, bh))

    return boxes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True, help="Folder of source images")
    parser.add_argument("--masks", required=True, help="Folder of matching mask PNGs")
    parser.add_argument("--out", required=True, help="Output flat folder (created)")
    parser.add_argument("--class-id", type=int, default=0, help="Placeholder class id to write")
    args = parser.parse_args()

    images_dir = Path(args.images)
    masks_dir = Path(args.masks)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    image_files = sorted(p for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)

    converted = 0
    empty_skipped = 0
    no_mask_found = 0

    for img_path in image_files:
        # masks are named label_<n>.png while images are e.g. image_<n>.jpg —
        # match on the trailing number rather than assuming identical stems.
        stem_num = "".join(ch for ch in img_path.stem if ch.isdigit())
        candidates = list(masks_dir.glob(f"*{stem_num}.png")) if stem_num else []
        mask_path = candidates[0] if candidates else (masks_dir / (img_path.stem + ".png"))

        if not mask_path.exists():
            no_mask_found += 1
            continue

        mask = np.array(Image.open(mask_path))
        boxes = mask_to_boxes(mask)

        if not boxes:
            empty_skipped += 1
            continue

        shutil.copy2(img_path, out_dir / img_path.name)
        lines = [f"{args.class_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}" for xc, yc, bw, bh in boxes]
        (out_dir / (img_path.stem + ".txt")).write_text("\n".join(lines) + "\n")
        converted += 1

    print(f"Converted: {converted}")
    print(f"Skipped (mask all-zero, no flooding visible): {empty_skipped}")
    print(f"Skipped (no matching mask file found): {no_mask_found}")
    print(f"Output written to: {out_dir}")


if __name__ == "__main__":
    main()
