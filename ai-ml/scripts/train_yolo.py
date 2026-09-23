"""
Trains a YOLOv8 model on the CiviSense 8-class dataset.

This does REAL training — it will take real time (hours, not minutes, on a
Mac CPU; much faster with a GPU e.g. free Google Colab). There is no shortcut
that produces a genuinely trained model instantly. Do not interrupt it
expecting a finished model in seconds.

Before running this:
  1. scripts/audit_dataset.py must show no structural problems.
  2. Ideally scripts/oversample_rare_classes.py has been run, so rare classes
     (illegal_parking, waterlogging, speed_breaker, open_manhole) aren't
     drowned out by garbage (59k+ boxes).

Usage:
    python3 scripts/train_yolo.py                      # sensible defaults
    python3 scripts/train_yolo.py --epochs 50 --imgsz 640 --model yolov8n.pt

Output: a trained weights file at models/best.pt — this is what
backend/ai/*.py will load. Until this file exists, the backend correctly
reports severity/priority as "unavailable" (see ai-ml/README.md).
"""

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

AI_ML_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(AI_ML_ROOT / "database" / "data.yaml"))
    parser.add_argument("--model", default="yolov8n.pt",
                         help="Base model to fine-tune. yolov8n.pt is smallest/fastest "
                              "(good for a CPU laptop); yolov8s.pt is more accurate but slower.")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default=None,
                         help="'cpu', 'mps' (Mac GPU), or a CUDA device index. "
                              "Leave unset to let Ultralytics auto-pick.")
    args = parser.parse_args()

    data_yaml = Path(args.data)
    if not data_yaml.exists():
        print(f"ERROR: {data_yaml} not found. Run scripts/audit_dataset.py first.")
        return

    print(f"Starting training: model={args.model}, epochs={args.epochs}, "
          f"imgsz={args.imgsz}, batch={args.batch}")
    print("This is real training — expect it to take a while. Progress will "
          "print per epoch below; do not assume it has failed if it's slow.\n")

    model = YOLO(args.model)
    results = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=str(AI_ML_ROOT / "runs"),
        name="civisense",
        exist_ok=True,
    )

    # Ultralytics writes the best checkpoint under runs/civisense/weights/best.pt
    best_weights = AI_ML_ROOT / "runs" / "civisense" / "weights" / "best.pt"
    models_dir = AI_ML_ROOT / "models"
    models_dir.mkdir(exist_ok=True)

    if best_weights.exists():
        dest = models_dir / "best.pt"
        shutil.copy2(best_weights, dest)
        print(f"\nTraining complete. Best weights copied to: {dest}")
        print("This is now what backend/ai/*.py should load for real inference.")
    else:
        print(f"\nWARNING: expected weights at {best_weights} but didn't find them. "
              "Check the runs/civisense/ folder for what was actually produced — "
              "do not assume training succeeded.")

    print("\nNext: run scripts/evaluate_model.py to see real per-class accuracy "
          "(precision/recall/mAP) — do not report the model as 'working' without it.")


if __name__ == "__main__":
    main()
