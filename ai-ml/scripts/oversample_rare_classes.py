"""
Duplicates training images that contain rare classes, so YOLO sees them
more often per epoch. This is the standard fix for severe class imbalance
(our garbage:illegal_parking ratio is ~700:1).

IMPORTANT: only touches database/images/train and database/labels/train.
val/ and test/ are left untouched on purpose — they must reflect the real
class distribution so evaluation numbers are honest, not inflated.

How it decides what to duplicate: for each class, if its box count is below
--target, it repeatedly duplicates images containing that class (copies with
a new filename, doesn't touch the original) until the class reaches roughly
--target boxes, or --max-copies per source image is hit (to avoid a single
image being cloned hundreds of times and dominating the dataset).

Usage:
    python3 scripts/oversample_rare_classes.py --target 5000 --max-copies 15

Run scripts/audit_dataset.py again afterwards to see the new balance.
"""

import argparse
import shutil
from collections import defaultdict
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "database"
CLASS_NAMES = [
    "pothole", "speed_breaker", "unpaved_road", "garbage",
    "waterlogging", "open_manhole", "damaged_road_sign", "illegal_parking",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=5000, help="Target box count per class")
    parser.add_argument("--max-copies", type=int, default=15, help="Max duplicates per source image")
    args = parser.parse_args()

    img_dir = DB / "images" / "train"
    lbl_dir = DB / "labels" / "train"

    # index: which images contain which classes, and current box counts
    images_with_class = defaultdict(list)
    class_counts = defaultdict(int)

    label_files = list(lbl_dir.glob("*.txt"))
    for lbl_path in label_files:
        img_path = None
        for ext in (".jpg", ".jpeg", ".png"):
            candidate = img_dir / (lbl_path.stem + ext)
            if candidate.exists():
                img_path = candidate
                break
        if img_path is None:
            continue

        classes_in_image = set()
        for line in lbl_path.read_text().splitlines():
            parts = line.split()
            if not parts:
                continue
            cls = int(parts[0])
            class_counts[cls] += 1
            classes_in_image.add(cls)

        for cls in classes_in_image:
            images_with_class[cls].append((img_path, lbl_path))

    print("Current train box counts:")
    for i, name in enumerate(CLASS_NAMES):
        print(f"  {name:<18} {class_counts.get(i, 0)}")

    total_added = 0
    for cls, name in enumerate(CLASS_NAMES):
        current = class_counts.get(cls, 0)
        if current == 0:
            print(f"\nSkipping '{name}': zero examples, oversampling can't fix missing data.")
            continue
        if current >= args.target:
            continue

        pool = images_with_class[cls]
        needed = args.target - current
        boxes_per_image = current / len(pool)  # average boxes of this class per source image
        copies_needed = int(needed / boxes_per_image) + 1
        copies_per_image = min(args.max_copies, max(1, copies_needed // len(pool) + 1))

        print(f"\n'{name}': {current} -> targeting {args.target}. "
              f"Duplicating {len(pool)} source images up to {copies_per_image}x each.")

        added = 0
        for img_path, lbl_path in pool:
            for copy_num in range(copies_per_image):
                if class_counts[cls] + added >= args.target:
                    break
                new_stem = f"{img_path.stem}_dup{copy_num}"
                new_img = img_dir / f"{new_stem}{img_path.suffix}"
                new_lbl = lbl_dir / f"{new_stem}.txt"
                if new_img.exists():
                    continue
                shutil.copy2(img_path, new_img)
                shutil.copy2(lbl_path, new_lbl)
                # count every box in the duplicated label, not just this class,
                # since oversampling one class also boosts co-occurring classes
                for line in lbl_path.read_text().splitlines():
                    if line.split():
                        added += 1
            if class_counts[cls] + added >= args.target:
                break

        total_added += added

    print(f"\nDone. {total_added} new (image, label) duplicate pairs added to train/.")
    print("Run scripts/audit_dataset.py to see the updated balance.")


if __name__ == "__main__":
    main()
