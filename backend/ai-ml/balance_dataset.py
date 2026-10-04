"""
balance_dataset.py

Builds a balanced COPY of a YOLO dataset by cutting down the over-represented
class (garbage). Your original dataset is never changed. The val and test
splits are copied as they are, so your accuracy numbers stay honest.

Rule used for the train split:
  - Any image that has at least one non-garbage object is KEPT (so every
    pothole, speed breaker, etc. image stays).
  - Images that contain ONLY garbage are randomly sampled down to a limit.
  - A few empty (background) images are kept, to help reduce false alarms.

Step 1 - look at the numbers only:
  python balance_dataset.py --data /path/to/data.yaml --audit-only

Step 2 - build the balanced copy:
  python balance_dataset.py --data /path/to/data.yaml \
      --out /path/to/dataset_balanced --max-garbage-images 1500
"""
import argparse
import random
import shutil
from collections import Counter
from pathlib import Path

import yaml

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def class_names(cfg):
    names = cfg["names"]
    if isinstance(names, dict):
        return {int(k): v for k, v in names.items()}
    return {i: n for i, n in enumerate(names)}


def split_dir(cfg, yaml_path, key):
    """Return the images folder for a split (train / val / test), or None."""
    rel = cfg.get(key)
    if rel is None:
        return None
    root = Path(cfg.get("path", yaml_path.parent))
    if not root.is_absolute():
        root = (yaml_path.parent / root).resolve()
    d = Path(rel)
    return d if d.is_absolute() else root / d


def label_path_for(img):
    """Swap the last 'images' folder in the path for 'labels'."""
    parts = list(img.parts)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "images":
            parts[i] = "labels"
            break
    return Path(*parts).with_suffix(".txt")


def read_classes(label_file):
    if not label_file.exists():
        return []
    out = []
    for line in label_file.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(int(line.split()[0]))
    return out


def scan(img_dir):
    """List of (image_path, label_path, [class ids]) for one split."""
    items = []
    for img in sorted(img_dir.rglob("*")):
        if img.suffix.lower() in IMG_EXT:
            lbl = label_path_for(img)
            items.append((img, lbl, read_classes(lbl)))
    return items


def print_counts(title, items, names):
    boxes = Counter()
    images = Counter()
    for _, _, classes in items:
        boxes.update(classes)
        images.update(set(classes))
    empty = sum(1 for _, _, c in items if not c)
    print(f"\n{title}: {len(items)} images ({empty} with no objects)")
    print(f"  {'class':<18}{'boxes':>10}{'images':>10}")
    for cid in sorted(names):
        print(f"  {names[cid]:<18}{boxes[cid]:>10}{images[cid]:>10}")


def copy_pair(img, lbl, out_root, split):
    img_out = out_root / "images" / split
    lbl_out = out_root / "labels" / split
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(img, img_out / img.name)
    if lbl.exists():
        shutil.copy2(lbl, lbl_out / lbl.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="path to the dataset data.yaml")
    ap.add_argument("--out", help="folder for the balanced copy")
    ap.add_argument("--majority", default="garbage", help="class name to cut down")
    ap.add_argument("--max-garbage-images", type=int, default=1500)
    ap.add_argument("--max-background", type=int, default=200)
    ap.add_argument("--audit-only", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    yaml_path = Path(args.data).resolve()
    cfg = load_yaml(yaml_path)
    names = class_names(cfg)

    splits = {}
    for key in ("train", "val", "test"):
        d = split_dir(cfg, yaml_path, key)
        if d is not None and d.exists():
            splits[key] = scan(d)

    if "train" not in splits:
        raise SystemExit("Could not find the train images folder. Check data.yaml.")

    for key, items in splits.items():
        print_counts(f"[{key}]", items, names)

    if args.audit_only:
        print("\nAudit only - nothing was written.")
        print("Check that val has some images of EVERY class, otherwise the "
              "accuracy for that class cannot be trusted.")
        return

    if not args.out:
        raise SystemExit("Give --out so I know where to write the balanced copy.")

    major_ids = [cid for cid, n in names.items() if n == args.majority]
    if not major_ids:
        raise SystemExit(f"No class called '{args.majority}'. Classes: {list(names.values())}")
    major = major_ids[0]

    random.seed(args.seed)
    out_root = Path(args.out).resolve()
    if out_root.exists():
        raise SystemExit(f"{out_root} already exists. Pick a new folder or delete it first.")

    train = splits["train"]
    keep_other = [t for t in train if any(c != major for c in t[2])]
    only_major = [t for t in train if t[2] and all(c == major for c in t[2])]
    background = [t for t in train if not t[2]]

    random.shuffle(only_major)
    random.shuffle(background)
    kept_major = only_major[: args.max_garbage_images]
    kept_bg = background[: args.max_background]

    kept_train = keep_other + kept_major + kept_bg
    print(f"\nTrain images kept: {len(kept_train)}")
    print(f"  with other classes (all kept): {len(keep_other)}")
    print(f"  {args.majority}-only (kept {len(kept_major)} of {len(only_major)})")
    print(f"  background (kept {len(kept_bg)} of {len(background)})")

    for img, lbl, _ in kept_train:
        copy_pair(img, lbl, out_root, "train")
    for key in ("val", "test"):
        for img, lbl, _ in splits.get(key, []):
            copy_pair(img, lbl, out_root, key)

    new_cfg = {
        "path": str(out_root),
        "train": "images/train",
        "val": "images/val" if "val" in splits else "images/train",
        "names": names,
    }
    if "test" in splits:
        new_cfg["test"] = "images/test"
    with open(out_root / "data.yaml", "w") as f:
        yaml.safe_dump(new_cfg, f, sort_keys=False)

    print_counts("[train AFTER balancing]", kept_train, names)
    print(f"\nDone. New dataset: {out_root}")
    print(f"Train with: data={out_root / 'data.yaml'}")


if __name__ == "__main__":
    main()
