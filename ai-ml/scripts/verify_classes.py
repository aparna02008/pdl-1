"""
Draws bounding boxes from a few sample label files onto their images, so you
can look at them and confirm what class 0 / 1 / 2 actually is — instead of
guessing from filenames.

Run from Dataset3Class/ folder:
    python3 verify_classes.py

Output: a folder 'class_samples/' with a few example images per class,
boxes drawn in red with the class number printed on them.
"""

import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SRC = Path(".")
OUT = Path("class_samples")
SAMPLES_PER_CLASS = 6

def main():
    OUT.mkdir(exist_ok=True)
    label_files = list(SRC.glob("*.txt"))
    by_class = {0: [], 1: [], 2: []}

    for lbl in label_files:
        img = SRC / (lbl.stem + ".jpg")
        if not img.exists():
            continue
        for line in lbl.read_text().splitlines():
            parts = line.split()
            if not parts:
                continue
            cls = int(parts[0])
            if cls in by_class and len(by_class[cls]) < SAMPLES_PER_CLASS * 3:
                by_class[cls].append((img, lbl))

    for cls, pairs in by_class.items():
        random.shuffle(pairs)
        for i, (img_path, lbl_path) in enumerate(pairs[:SAMPLES_PER_CLASS]):
            im = Image.open(img_path).convert("RGB")
            w, h = im.size
            draw = ImageDraw.Draw(im)
            for line in lbl_path.read_text().splitlines():
                parts = line.split()
                if not parts:
                    continue
                c, xc, yc, bw, bh = int(parts[0]), *map(float, parts[1:5])
                x1 = (xc - bw / 2) * w
                y1 = (yc - bh / 2) * h
                x2 = (xc + bw / 2) * w
                y2 = (yc + bh / 2) * h
                color = "red" if c == cls else "yellow"
                draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
                draw.text((x1, max(0, y1 - 14)), f"class {c}", fill=color)

            out_path = OUT / f"class{cls}_{i}_{img_path.name}"
            im.save(out_path)

    print(f"Saved samples to {OUT}/ — open the folder and look at a few from each class group.")
    for cls in (0, 1, 2):
        print(f"  class {cls}: {min(len(by_class[cls]), SAMPLES_PER_CLASS)} samples saved (class{cls}_*.jpg)")


if __name__ == "__main__":
    main()
