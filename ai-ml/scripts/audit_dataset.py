"""
Dataset audit for CiviSense (pothole / speed_breaker / unpaved_road).

What this does — nothing more, nothing less:
  1. Reads database/data.yaml to get class names and split paths.
  2. For each split (train/val/test), walks the images folder and checks:
       - does a matching .txt label file exist?
       - is the label file empty (no boxes)?
       - are class indices inside it valid (0..nc-1)?
       - is each image file actually openable (not corrupt/truncated)?
       - real per-class box counts.
  3. Prints a plain summary table. Does NOT train anything, does NOT decide
     "your dataset is fine" — it just reports what's actually on disk so you
     can decide what to do next.

Run:
    python scripts/audit_dataset.py
    python scripts/audit_dataset.py --data database/data.yaml
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import yaml
from PIL import Image, UnidentifiedImageError

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def load_data_yaml(path: Path) -> dict:
    if not path.exists():
        print(f"ERROR: {path} not found. Nothing to audit yet.")
        print("Expected a YOLO-style data.yaml with 'train'/'val'/'test' image dirs and 'names'.")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def labels_dir_for(images_dir: Path) -> Path:
    """Standard YOLO convention: .../images/<split> -> .../labels/<split>."""
    parts = list(images_dir.parts)
    if "images" in parts:
        idx = parts.index("images")
        parts[idx] = "labels"
        return Path(*parts)
    # Fallback: sibling 'labels' folder next to 'images'
    return images_dir.parent.parent / "labels" / images_dir.name


def audit_split(split_name: str, images_dir: Path, num_classes: int, class_names: list[str]) -> dict:
    result = {
        "split": split_name,
        "images_found": 0,
        "images_missing_label": [],
        "labels_empty": [],
        "labels_invalid_class": [],
        "corrupt_images": [],
        "class_box_counts": defaultdict(int),
    }

    if not images_dir.exists():
        result["dir_missing"] = True
        return result
    result["dir_missing"] = False

    labels_dir = labels_dir_for(images_dir)
    image_files = sorted(p for p in images_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    result["images_found"] = len(image_files)

    for img_path in image_files:
        # Corrupt/truncated image check — actually opens and decodes it.
        try:
            with Image.open(img_path) as im:
                im.verify()
        except (UnidentifiedImageError, OSError):
            result["corrupt_images"].append(str(img_path))

        label_path = labels_dir / (img_path.stem + ".txt")
        if not label_path.exists():
            result["images_missing_label"].append(str(img_path))
            continue

        lines = [l.strip() for l in label_path.read_text().splitlines() if l.strip()]
        if not lines:
            result["labels_empty"].append(str(label_path))
            continue

        for line in lines:
            fields = line.split()
            if not fields:
                continue
            try:
                cls_idx = int(fields[0])
            except ValueError:
                result["labels_invalid_class"].append((str(label_path), line))
                continue
            if cls_idx < 0 or cls_idx >= num_classes:
                result["labels_invalid_class"].append((str(label_path), line))
                continue
            result["class_box_counts"][class_names[cls_idx]] += 1

    return result


def print_report(reports: list[dict], class_names: list[str]):
    print("=" * 70)
    print("CIVISENSE DATASET AUDIT")
    print("=" * 70)

    for r in reports:
        print(f"\n[{r['split'].upper()}]")
        if r.get("dir_missing"):
            print("  Directory not found on disk — nothing to audit for this split.")
            continue

        print(f"  Images found:            {r['images_found']}")
        print(f"  Images missing a label:  {len(r['images_missing_label'])}")
        print(f"  Empty label files:       {len(r['labels_empty'])}")
        print(f"  Invalid class indices:   {len(r['labels_invalid_class'])}")
        print(f"  Corrupt/unreadable imgs: {len(r['corrupt_images'])}")
        print("  Box counts per class:")
        for name in class_names:
            print(f"    {name:<16} {r['class_box_counts'].get(name, 0)}")

        if r["images_missing_label"][:5]:
            print("  First few images missing labels:")
            for p in r["images_missing_label"][:5]:
                print(f"    - {p}")
        if r["corrupt_images"][:5]:
            print("  First few corrupt images:")
            for p in r["corrupt_images"][:5]:
                print(f"    - {p}")

    print("\n" + "=" * 70)
    print("VERDICT (facts only — you decide what to do next)")
    print("=" * 70)

    train_report = next((r for r in reports if r["split"] == "train"), None)
    problems = []

    if train_report and not train_report.get("dir_missing"):
        for name in class_names:
            if train_report["class_box_counts"].get(name, 0) == 0:
                problems.append(f"'{name}' has ZERO labeled examples in the train split.")
    else:
        problems.append("Train split directory is missing or empty — no training is possible yet.")

    total_corrupt = sum(len(r.get("corrupt_images", [])) for r in reports)
    if total_corrupt:
        problems.append(f"{total_corrupt} image file(s) across all splits are corrupt/unreadable.")

    total_missing_labels = sum(len(r.get("images_missing_label", [])) for r in reports)
    if total_missing_labels:
        problems.append(f"{total_missing_labels} image(s) across all splits have no matching label file.")

    if problems:
        print("NOT ready to train. Issues found:")
        for p in problems:
            print(f"  - {p}")
        print("\nFix these on disk first (collect more data, re-label, or remove")
        print("corrupt files) — do not proceed to YOLO training until this is clean.")
    else:
        print("No structural problems found (every class has train examples,")
        print("no corrupt images, no missing labels). This does NOT guarantee")
        print("the dataset is large enough or well-balanced — only that it's")
        print("structurally sound to start training on.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="database/data.yaml", help="Path to data.yaml")
    args = parser.parse_args()

    data_yaml_path = Path(args.data)
    config = load_data_yaml(data_yaml_path)

    class_names = config.get("names")
    if isinstance(class_names, dict):
        class_names = [class_names[i] for i in sorted(class_names)]
    num_classes = config.get("nc", len(class_names) if class_names else 0)

    if not class_names:
        print("ERROR: data.yaml has no 'names' list. Cannot map class indices to labels.")
        sys.exit(1)

    base_dir = data_yaml_path.parent
    reports = []
    for split_key in ("train", "val", "test"):
        raw_path = config.get(split_key)
        if not raw_path:
            continue
        images_dir = (base_dir / raw_path).resolve()
        reports.append(audit_split(split_key, images_dir, num_classes, class_names))

    print_report(reports, class_names)


if __name__ == "__main__":
    main()
