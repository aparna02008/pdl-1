"""
Priority prediction — intended to answer "how urgently should this
complaint be handled relative to others?" using XGBoost, combining
category, severity, location, recurrence, and other real signals.

HONESTY NOTE: same situation as severity.py. A real priority model needs
real labeled priority data (complaints where a human/authority actually
assigned a priority level, or resolution-time data to learn from). That
dataset does not exist yet. This module returns "unavailable" until a
real model is trained — no fabricated priority scores.
"""

import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "priority_model.joblib")


def predict_priority(features: dict) -> dict:
    """
    features is expected to eventually include real signals such as:
    {
        "category": "pothole",
        "confidence": 0.87,
        "relative_size": 0.12,
        "severity": "High",            # once severity.py is real
        "is_recurrence": True,
        "days_since_similar_reports": 2,
        ...
    }

    Returns:
    {
        "status": "unavailable",
        "reason": "no trained priority model present",
        "priority": None
    }

    Never returns a fabricated priority — see train_priority_model() below
    for what's needed to make this real.
    """
    if not os.path.exists(MODEL_PATH):
        return {
            "status": "unavailable",
            "reason": "no trained priority model present",
            "priority": None,
        }

    model = joblib.load(MODEL_PATH)
    feature_vector = _features_to_vector(features)
    prediction = model.predict([feature_vector])[0]
    return {"status": "ok", "reason": None, "priority": prediction}


def _features_to_vector(features: dict) -> list:
    raise NotImplementedError(
        "Define the real feature vector once priority_model.joblib exists "
        "and you know what features it was trained on."
    )


def train_priority_model(labeled_csv_path: str):
    """
    Needed for a real priority model:

        complaint_id, category, confidence, relative_size, severity,
        is_recurrence, location_features, ..., priority_label

    Two realistic ways to get real labels (don't invent a third):
    1. Human-assigned: an authority actually marks each historical
       complaint's priority (Low/Medium/High/Critical) on review.
    2. Outcome-derived: use real resolution-time data as a proxy — e.g.
       complaints resolved fastest were implicitly treated as higher
       priority by the authority handling them. This is weaker (proxy,
       not ground truth) but can bootstrap a first model if no manual
       labels exist, AS LONG AS this derivation is documented honestly
       wherever the resulting priority score is shown.

    Steps once real labeled data exists:
        1. Load and engineer features — reuse severity.py's output once
           that's real, don't duplicate severity logic here.
        2. Train XGBoost classifier (xgboost.XGBClassifier) — priority is
           ordinal (Low < Medium < High < Critical), consider
           xgboost's objective='multi:softprob' or an ordinal-aware setup.
        3. Evaluate against a held-out split; compare to a majority-class
           and a random baseline before trusting it.
        4. joblib.dump(trained_model, MODEL_PATH)
        5. Wire up explainability.py (SHAP TreeExplainer) against this
           exact model — SHAP explanations are only meaningful against a
           real trained model, never fabricated alongside a fake score.

    Raises until that pipeline exists.
    """
    raise NotImplementedError(
        "Priority training requires real labeled data — see docstring "
        "above. Not implemented yet because that dataset doesn't exist."
    )


if __name__ == "__main__":
    print(predict_priority({"category": "pothole", "confidence": 0.87}))
