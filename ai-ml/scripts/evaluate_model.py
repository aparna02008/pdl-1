"""
Runs real evaluation of a trained model against the test split, and prints
per-class precision, recall, and mAP50. This is the ONLY honest way to know
if training worked — do not report a model as "accurate" without running
this first.

Usage:
    python3 scripts/evaluate_model.py
    python3 scripts/evaluate_model.py --weights models/best.pt
"""

import argparse
from pathlib import Path

from ultralytics import YOLO

AI_ML_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", default=str(AI_ML_ROOT / "models" / "best.pt"))
    parser.add_argument("--data", default=str(AI_ML_ROOT / "database" / "data.yaml"))
    parser.add_argument("--split", default="test", choices=["val", "test"])
    args = parser.parse_args()

    weights_path = Path(args.weights)
    if not weights_path.exists():
        print(f"ERROR: no trained model found at {weights_path}.")
        print("Run scripts/train_yolo.py first — there is nothing to evaluate yet.")
        return

    model = YOLO(str(weights_path))
    metrics = model.val(data=args.data, split=args.split)

    print("\n" + "=" * 60)
    print(f"REAL EVALUATION RESULTS ({args.split} split)")
    print("=" * 60)
    print(f"Overall mAP50:    {metrics.box.map50:.3f}")
    print(f"Overall mAP50-95: {metrics.box.map:.3f}")
    print("\nPer-class (precision, recall, mAP50):")

    class_names = model.names
    for i, name in class_names.items():
        try:
            p = metrics.box.p[i]
            r = metrics.box.r[i]
            ap50 = metrics.box.ap50[i]
            print(f"  {name:<18} precision={p:.3f}  recall={r:.3f}  mAP50={ap50:.3f}")
        except (IndexError, KeyError):
            print(f"  {name:<18} no predictions/ground truth to score")

    print("\nA low score for a class (especially illegal_parking, which had the")
    print("least training data) is expected and honest — it means the model")
    print("genuinely isn't reliable for that class yet, not that something is broken.")


if __name__ == "__main__":
    main()
