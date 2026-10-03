"""Train XGBoost severity + priority models for CiviSense.

Run from the repo root with the venv active:
    python ai-ml/scripts/train_severity_priority.py

Inputs : backend/civisense.db (descriptions) + backend/labels_final.csv (labels)
Output : ai-ml/models/severity_priority_bundle.joblib

Priority = severity + location bump (labeling_rules.txt), so the priority
model also receives the severity model's probabilities as features.
"""
import re
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "backend" / "civisense.db"
LABELS_PATH = ROOT / "backend" / "labels_final.csv"
OUT_DIR = ROOT / "ai-ml" / "models"
OUT_PATH = OUT_DIR / "severity_priority_bundle.joblib"

# Locations that bump priority by +1 (see labeling_rules.txt).
# These are handled by explicit flags, not by TF-IDF words.
FLAG_PATTERNS = {
    "near_school": r"\bschool\b",
    "near_health_centre": r"health centre",
    "near_junction": r"\bjunction\b",
    "near_main_crossing": r"main road crossing",
}

# Words that only describe WHERE or are sentence filler. They say nothing about
# how serious the issue is, so the text model should not learn from them.
CUSTOM_STOP_WORDS = [
    "near", "outside", "beside", "along", "road", "street", "stretch", "part",
    "side", "area", "school", "gate", "bus", "stop", "market", "entrance",
    "local", "park", "railway", "station", "approach", "temple", "tank",
    "community", "health", "centre", "junction", "main", "crossing", "demo",
    "formed", "opened", "come", "came", "appears", "making", "creating",
]
STOP_WORDS = sorted(set(ENGLISH_STOP_WORDS) | set(CUSTOM_STOP_WORDS))


def clean(text: str) -> str:
    return re.sub(r"^\[DEMO\]\s*", "", str(text or "")).lower()


def build_features(descriptions, vectorizer, fit=False):
    """Return (tfidf, flags). Same function must be used at inference time."""
    texts = [clean(d) for d in descriptions]
    tfidf = vectorizer.fit_transform(texts) if fit else vectorizer.transform(texts)
    tfidf = tfidf.toarray()
    flags = np.array(
        [[1 if re.search(p, t) else 0 for p in FLAG_PATTERNS.values()] for t in texts]
    )
    return tfidf, flags


def assemble(descriptions, reported_categories, all_categories, vectorizer, fit=False):
    tfidf, flags = build_features(descriptions, vectorizer, fit=fit)
    cat = np.array(
        [[1 if rc == c else 0 for c in all_categories] for rc in reported_categories]
    )
    names = (
        [f"word:{w}" for w in vectorizer.get_feature_names_out()]
        + list(FLAG_PATTERNS.keys())
        + [f"cat:{c}" for c in all_categories]
    )
    return np.hstack([tfidf, flags, cat]), names


def make_model():
    return XGBClassifier(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.1,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42,
    )


def show(name, y, pred):
    print(f"\n=== {name} (5-fold cross-validation) ===")
    print("accuracy:", round(accuracy_score(y, pred), 3))
    print(classification_report(y, pred, target_names=["1", "2", "3"], zero_division=0))


def main():
    with sqlite3.connect(DB_PATH) as conn:
        db = pd.read_sql_query(
            "select id as complaint_id, description, reported_category from complaints", conn
        )
    labels = pd.read_csv(LABELS_PATH)
    df = labels.merge(db, on="complaint_id", how="left")

    missing = df["description"].isna().sum()
    if missing:
        raise SystemExit(f"{missing} labeled rows not found in the DB (check complaint_id)")
    df["reported_category"] = df["reported_category"].fillna(df["category"])
    print(f"Rows: {len(df)}")

    all_categories = sorted(df["reported_category"].unique())
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 1), min_df=2, max_features=150, stop_words=STOP_WORDS
    )
    X, feature_names = assemble(
        df["description"], df["reported_category"], all_categories, vectorizer, fit=True
    )
    print(f"Features: {X.shape[1]}")

    y_sev = df["severity"].astype(int).values - 1  # XGBoost wants 0..2
    y_pri = df["priority"].astype(int).values - 1
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Severity model
    sev_oof = cross_val_predict(make_model(), X, y_sev, cv=cv, method="predict_proba")
    show("severity", y_sev, sev_oof.argmax(axis=1))
    sev_model = make_model().fit(X, y_sev)

    # Priority model: text/location features + severity probabilities
    X_pri = np.hstack([X, sev_oof])
    pri_oof = cross_val_predict(make_model(), X_pri, y_pri, cv=cv)
    show("priority", y_pri, pri_oof)
    pri_model = make_model().fit(X_pri, y_pri)
    pri_names = feature_names + ["sev_proba_1", "sev_proba_2", "sev_proba_3"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "vectorizer": vectorizer,
            "categories": all_categories,
            "feature_names": feature_names,
            "priority_feature_names": pri_names,
            "severity_model": sev_model,
            "priority_model": pri_model,
        },
        OUT_PATH,
    )
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()