"""SHAP explanations for the CiviSense severity + priority models.

Usage (repo root, venv active):
    python ai-ml/scripts/explain_shap.py "Deep pothole near the school gate" pothole
    python ai-ml/scripts/explain_shap.py --global

Import in other code:
    from explain_shap import SeverityPriorityExplainer
    result = SeverityPriorityExplainer().explain(description, category)
"""
import sqlite3
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_severity_priority import DB_PATH, LABELS_PATH, OUT_DIR, OUT_PATH, assemble  # noqa: E402


def _class_values(sv, cls):
    """SHAP values of one sample for one class (handles old and new shap formats)."""
    if isinstance(sv, list):
        return np.asarray(sv[cls])[0]
    sv = np.asarray(sv)
    if sv.ndim == 3:
        return sv[0, :, cls]
    return sv[0]


def _pretty(name):
    if name.startswith("word:"):
        return f'word "{name[5:]}"'
    if name.startswith("cat:"):
        return f"category: {name[4:]}"
    if name.startswith("near_"):
        return name.replace("_", " ")
    if name.startswith("sev_proba_"):
        return f"severity model score for level {name[-1]}"
    return name


def _top(values, names, top_k):
    out = []
    for i in np.argsort(-np.abs(values))[:top_k]:
        if abs(values[i]) < 1e-6:
            continue
        out.append(
            {
                "feature": _pretty(names[i]),
                "impact": round(float(values[i]), 4),
                "direction": "raises" if values[i] > 0 else "lowers",
            }
        )
    return out


class SeverityPriorityExplainer:
    def __init__(self, path=OUT_PATH):
        self.b = joblib.load(path)
        self.sev_exp = shap.TreeExplainer(self.b["severity_model"])
        self.pri_exp = shap.TreeExplainer(self.b["priority_model"])

    def explain(self, description, category, top_k=5):
        b = self.b
        X, _ = assemble([description], [category], b["categories"], b["vectorizer"], fit=False)

        sev_proba = b["severity_model"].predict_proba(X)
        sev_cls = int(sev_proba.argmax())
        X_pri = np.hstack([X, sev_proba])
        pri_proba = b["priority_model"].predict_proba(X_pri)
        pri_cls = int(pri_proba.argmax())

        sev_vals = _class_values(self.sev_exp.shap_values(X), sev_cls)
        pri_vals = _class_values(self.pri_exp.shap_values(X_pri), pri_cls)

        return {
            "severity": sev_cls + 1,
            "severity_confidence": round(float(sev_proba[0, sev_cls]), 3),
            "severity_reasons": _top(sev_vals, b["feature_names"], top_k),
            "priority": pri_cls + 1,
            "priority_confidence": round(float(pri_proba[0, pri_cls]), 3),
            "priority_reasons": _top(pri_vals, b["priority_feature_names"], top_k),
        }


def global_importance():
    ex = SeverityPriorityExplainer()
    b = ex.b
    with sqlite3.connect(DB_PATH) as conn:
        db = pd.read_sql_query(
            "select id as complaint_id, description, reported_category from complaints", conn
        )
    df = pd.read_csv(LABELS_PATH).merge(db, on="complaint_id", how="left")
    df["reported_category"] = df["reported_category"].fillna(df["category"])
    X, _ = assemble(df["description"], df["reported_category"], b["categories"], b["vectorizer"])
    X_pri = np.hstack([X, b["severity_model"].predict_proba(X)])

    def mean_abs(sv):
        if isinstance(sv, list):
            return np.mean([np.abs(s).mean(axis=0) for s in sv], axis=0)
        sv = np.asarray(sv)
        return np.abs(sv).mean(axis=(0, 2)) if sv.ndim == 3 else np.abs(sv).mean(axis=0)

    jobs = [
        ("severity", mean_abs(ex.sev_exp.shap_values(X)), b["feature_names"]),
        ("priority", mean_abs(ex.pri_exp.shap_values(X_pri)), b["priority_feature_names"]),
    ]
    for target, imp, names in jobs:
        order = np.argsort(-imp)[:10]
        print(f"\nTop features for {target}:")
        for i in order:
            print(f"  {_pretty(names[i]):45s} {imp[i]:.4f}")
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 5))
            ax.barh([_pretty(names[i]) for i in order][::-1], imp[order][::-1])
            ax.set_title(f"Top features: {target} (mean |SHAP|)")
            fig.tight_layout()
            path = OUT_DIR / f"shap_{target}_top_features.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            print(f"  saved {path}")
        except ImportError:
            print("  (pip install matplotlib to save the chart)")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--global":
        global_importance()
    elif len(sys.argv) >= 3:
        import json

        print(json.dumps(SeverityPriorityExplainer().explain(sys.argv[1], sys.argv[2]), indent=2))
    else:
        print(__doc__)