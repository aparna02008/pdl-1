"""
Merges one external dataset into ai-ml/database/, remapping its class
numbers to CiviSense's unified 8-class scheme first.

Why this exists: every Kaggle/Roboflow dataset invents its own class order
(their "0" might be our "3"). Copying files in directly without remapping
silently trains the model on wrong labels. This script is the one place
that remapping happens, so every merge goes through the same, checked path.

USAGE — you always tell it three things:
  1. --src         folder containing the source dataset's images + labels
                    (script auto-detects images/ + labels/ subfolders, or a
                    flat folder with both mixed together, same as
                    Dataset3Class was)
  2. --map         old_class_index:new_class_index pairs, comma separated.
                    Any class NOT listed is dropped (its boxes are removed,
                    image is kept only if it has other valid boxes).
  3. --split       ratios for train/val/test if the source has no existing
                    split, e.g. 0.8,0.1,0.1

Example — merging a garbage dataset where their class 0 = "garbage":
    python3 scripts/remap_and_merge.py \\
        --src ~/Downloads/garbage-detection \\
        --map 0:3 \\
        --split 0.8,0.1,0.1

Example — merging a dataset that already has its own train/val/test folders
and whose classes were [pothole, crack, manhole] (we only want manhole):
    python3 scripts/remap_and_merge.py \\
        --src ~/Downloads/road-damage-dataset \\
        --map 2:5

This NEVER overwrites database/. It copies files with a source-tag prefix
so filenames can't collide, and only appends.
"""

import argparse
import random
import shutil
import sys
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
DEST_BASE = Path(__file__).resolve().parent.parent / "database"


def find_pairs(src: Path) -> list[tuple[Path, Path]]:
    """Return (image_path, label_path) pairs, whether the source uses
    images/ + labels/ subfolders, images/<split> + labels/<split>, or one
    flat folder with both mixed together."""
    pairs = []

    # Case 1: flat folder, images and .txt mixed (like Dataset3Class)
    flat_images = [p for p in src.glob("*") if p.suffix.lower() in IMAGE_EXTS]
    if flat_images:
        for img in flat_images:
            lbl = img.with_suffix(".txt")
            if lbl.exists():
                pairs.append((img, lbl))
        if pairs:
            return pairs

    # Case 2: images/ and labels/ subfolders (possibly with train/val/test inside)
    images_root = src / "images"
    labels_root = src / "labels"
    if images_root.exists():
        for img in images_root.rglob("*"):
            if img.suffix.lower() not in IMAGE_EXTS:
                continue
            rel = img.relative_to(images_root)
            lbl = labels_root / rel.with_suffix(".txt")
            if lbl.exists():
                pairs.append((img, lbl))

    return pairs


def remap_label_lines(lines: list[str], mapping: dict[int, int]) -> list[str]:
    out = []
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        try:
            old_cls = int(parts[0])
        except ValueError:
            continue
        if old_cls not in mapping:
            continue  # drop boxes for classes we're not importing
        new_cls = mapping[old_cls]
        out.append(" ".join([str(new_cls)] + parts[1:]))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="Source dataset folder")
    parser.add_argument(
        "--map", required=True,
        help="old:new class index pairs, comma separated, e.g. 0:3,1:5"
    )
    parser.add_argument(
        "--split", default="0.8,0.1,0.1",
        help="train,val,test ratios used only if source has no split already"
    )
    parser.add_argument(
        "--tag", default=None,
        help="Prefix added to every copied filename to avoid collisions "
             "(default: source folder name)"
    )
    args = parser.parse_args()

    src = Path(args.src).expanduser().resolve()
    if not src.exists():
        print(f"ERROR: source folder {src} does not exist.")
        sys.exit(1)

    mapping = {}
    for pair in args.map.split(","):
        old, new = pair.split(":")
        mapping[int(old)] = int(new)

    tag = args.tag or src.name.replace(" ", "_")

    ratios = [float(x) for x in args.split.split(",")]
    if abs(sum(ratios) - 1.0) > 1e-6:
        print(f"ERROR: --split ratios must sum to 1.0, got {ratios}")
        sys.exit(1)

    pairs = find_pairs(src)
    if not pairs:
        print(f"ERROR: found no image+label pairs under {src}.")
        print("Expected either a flat folder with .jpg+.txt side by side,")
        print("or images/ and labels/ subfolders.")
        sys.exit(1)

    print(f"Found {len(pairs)} image+label pairs in {src}")

    random.seed(42)
    random.shuffle(pairs)
    n = len(pairs)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])
    splits = (
        [("train", p) for p in pairs[:n_train]]
        + [("val", p) for p in pairs[n_train:n_train + n_val]]
        + [("test", p) for p in pairs[n_train + n_val:]]
    )

    counts = {"train": 0, "val": 0, "test": 0}
    skipped_empty = 0

    for split, (img_path, lbl_path) in splits:
        lines = lbl_path.read_text().splitlines()
        new_lines = remap_label_lines(lines, mapping)
        if not new_lines:
            skipped_empty += 1
            continue  # nothing worth keeping from this image for our classes

        dest_img_dir = DEST_BASE / "images" / split
        dest_lbl_dir = DEST_BASE / "labels" / split
        dest_img_dir.mkdir(parents=True, exist_ok=True)
        dest_lbl_dir.mkdir(parents=True, exist_ok=True)

        new_name = f"{tag}_{img_path.stem}"
        shutil.copy2(img_path, dest_img_dir / f"{new_name}{img_path.suffix}")
        (dest_lbl_dir / f"{new_name}.txt").write_text("\n".join(new_lines) + "\n")
        counts[split] += 1

    print("\nMerge complete.")
    print(f"  train: +{counts['train']}  val: +{counts['val']}  test: +{counts['test']}")
    print(f"  skipped (no boxes in our target classes after remap): {skipped_empty}")
    print(f"\nRun scripts/audit_dataset.py next to see the updated class counts.")


if __name__ == "__main__":
    main()
