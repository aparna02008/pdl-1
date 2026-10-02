"""
Severity estimation — intended to answer "how serious is this issue?"
(e.g. a hairline crack vs. a road-swallowing pothole).

HONESTY NOTE (read this before touching this file):
A real severity model needs real labeled severity data — complaints where
a human has actually assessed and recorded "this was Low/Medium/High
severity". That dataset does not exist yet for this project. Rather than
fake a severity score from a heuristic and call it "AI", this module
returns an honest "unavailable" status until a real model is trained on
real labeled data. See train_severity_model() below for what's needed to
change that.

What this module CAN do today (not severity, kept separate on purpose):
- relative_size from yolo_detector.py's bbox-area-over-image-area is a
  weak proxy for "how big does the issue look in this photo", but it is
  NOT the same thing as severity (a small-looking pothole photographed
  up close can be more severe than a large-looking one photographed from
  far away). Don't substitute one for the other.
"""

import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "severity_model.joblib")


def estimate_severity(features: dict) -> dict:
    """
    features is expected to eventually look like:
    {
        "category": "pothole",
        "confidence": 0.87,
        "relative_size": 0.12,
        ... other real, measurable signals ...
    }

    Returns:
    {
        "status": "unavailable",
        "reason": "no trained severity model present",
        "severity": None
    }

    Once a real model exists at MODEL_PATH, this function will load it and
    return a real prediction. Until then it always returns "unavailable" —
    never a fabricated severity level, per the project's no-fake-AI rule.
    """
    if not os.path.exists(MODEL_PATH):
        return {
            "status": "unavailable",
            "reason": "no trained severity model present",
            "severity": None,
        }

    # This branch only runs once a real model file exists (see
    # train_severity_model.py). It is not reachable today.
    model = joblib.load(MODEL_PATH)
    feature_vector = _features_to_vector(features)
    prediction = model.predict([feature_vector])[0]
    return {"status": "ok", "reason": None, "severity": prediction}


def _features_to_vector(features: dict) -> list:
    """
    Placeholder feature encoding — fill this in once real training data
    defines what features the model actually uses (e.g. one-hot encoded
    category, confidence, relative_size, maybe recurrence count).
    """
    raise NotImplementedError(
        "Define the real feature vector once severity_model.joblib exists "
        "and you know what features it was trained on."
    )


# ---------------------------------------------------------------------------
# What would be needed to make this real (not run automatically — this is
# documentation + a stub so the next person knows exactly what's required):
# ---------------------------------------------------------------------------
def train_severity_model(labeled_csv_path: str):
    """
    To train a real severity model you need a CSV of REAL labeled examples:

        complaint_id, category, confidence, relative_size, ..., severity_label

    Where severity_label was assigned by an actual human reviewing the
    complaint (e.g. a municipal worker rating it Low/Medium/High), not
    guessed or synthesized.

    Minimum viable dataset: a few hundred labeled examples per category,
    ideally more. With fewer than ~100 total labeled examples, a trained
    model is unlikely to generalize — it's better to stay "unavailable"
    than to ship an overfit model that looks confident but isn't.

    Once you have that CSV:
        1. Load it with pandas.
        2. Engineer the same features _features_to_vector() will need to
           reproduce at inference time.
        3. Train a simple classifier (e.g. RandomForestClassifier or
           XGBoost) — severity is usually a small number of ordinal
           classes (Low/Medium/High/Critical), so a classifier, not a
           regressor, is the right starting point.
        4. Evaluate on a held-out test split. Only save the model to
           MODEL_PATH if accuracy/F1 on the held-out set is meaningfully
           better than a majority-class baseline.
        5. joblib.dump(trained_model, MODEL_PATH)

    This function intentionally raises until that real pipeline is built —
    it must not be called as a shortcut to produce a fake model.
    """
    raise NotImplementedError(
        "Severity training requires a real labeled dataset — see the "
        "docstring above for exactly what's needed. Not implemented yet "
        "because that dataset doesn't exist."
    )


if __name__ == "__main__":
    print(estimate_severity({"category": "pothole", "confidence": 0.87, "relative_size": 0.12}))
