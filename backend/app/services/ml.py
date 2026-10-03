"""Severity / priority prediction and SHAP explanations.

Loads the bundle trained by ai-ml/scripts/train_severity_priority.py.
If the model file or its libraries are missing, predict() returns None and the
caller must leave ai_status as "unavailable" (no fake AI output).
"""
import logging
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

BUNDLE_PATH = (
    Path(__file__).resolve().parents[3] / "ai-ml" / "models" / "severity_priority_bundle.joblib"
)

# Keep in sync with ai-ml/scripts/train_severity_priority.py
FLAG_PATTERNS = {
    "near_school": r"\bschool\b",
    "near_health_centre": r"health centre",
    "near_junction": r"\bjunction\b",
    "near_main_crossing": r"main road crossing",
}


def _clean(text):
    return re.sub(r"^\[DEMO\]\s*", "", str(text or "")).lower()


@lru_cache(maxsize=1)
def _load():
    if not BUNDLE_PATH.exists():
        logger.warning("ML bundle not found at %s", BUNDLE_PATH)
        return None
    try:
        import joblib

        return joblib.load(BUNDLE_PATH)
    except Exception:
        logger.exception("Could not load ML bundle")
        return None


@lru_cache(maxsize=1)
def _explainers():
    import shap

    b = _load()
    return shap.TreeExplainer(b["severity_model"]), shap.TreeExplainer(b["priority_model"])


def _features(description, category, b):
    text = _clean(description)
    tfidf = b["vectorizer"].transform([text]).toarray()
    flags = np.array([[1 if re.search(p, text) else 0 for p in FLAG_PATTERNS.values()]])
    cat = np.array([[1 if category == c else 0 for c in b["categories"]]])
    return np.hstack([tfidf, flags, cat])


def _score(description, category, b):
    X = _features(description, (category or "").strip(), b)
    sev_proba = b["severity_model"].predict_proba(X)
    X_pri = np.hstack([X, sev_proba])
    pri_proba = b["priority_model"].predict_proba(X_pri)
    return X, X_pri, sev_proba, pri_proba


def predict(description, category):
    """Return {severity, priority, *_confidence} (levels 1-3) or None if unavailable."""
    b = _load()
    if b is None:
        return None
    try:
        _, _, sev_proba, pri_proba = _score(description, category, b)
    except Exception:
        logger.exception("ML prediction failed")
        return None
    sev, pri = int(sev_proba.argmax()), int(pri_proba.argmax())
    return {
        "severity": sev + 1,
        "severity_confidence": round(float(sev_proba[0, sev]), 3),
        "priority": pri + 1,
        "priority_confidence": round(float(pri_proba[0, pri]), 3),
    }


def _class_values(sv, cls):
    if isinstance(sv, list):
        return np.asarray(sv[cls])[0]
    sv = np.asarray(sv)
    return sv[0, :, cls] if sv.ndim == 3 else sv[0]


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


def explain(description, category, top_k=5):
    """Prediction plus SHAP reasons, or None if the model is unavailable."""
    b = _load()
    if b is None:
        return None
    try:
        X, X_pri, sev_proba, pri_proba = _score(description, category, b)
    except Exception:
        logger.exception("ML prediction failed")
        return None

    sev, pri = int(sev_proba.argmax()), int(pri_proba.argmax())
    result = {
        "severity": sev + 1,
        "severity_confidence": round(float(sev_proba[0, sev]), 3),
        "severity_reasons": [],
        "priority": pri + 1,
        "priority_confidence": round(float(pri_proba[0, pri]), 3),
        "priority_reasons": [],
    }
    try:
        sev_exp, pri_exp = _explainers()
        result["severity_reasons"] = _top(
            _class_values(sev_exp.shap_values(X), sev), b["feature_names"], top_k
        )
        result["priority_reasons"] = _top(
            _class_values(pri_exp.shap_values(X_pri), pri), b["priority_feature_names"], top_k
        )
    except Exception:
        logger.exception("SHAP explanation failed")
    return result