"""
PredictV - learn fault ranking from real feedback.

Every time a rider reports what the mechanic actually found, the app stores
it next to the answers they gave. This script turns those rows into a
classifier (answers -> confirmed fault) and saves models/symptom_model.joblib.
The API picks it up on the next start and uses it to re-rank its results.

It refuses to train until there is enough real data. Nothing is generated.

Run from the project root:   npm run train:symptoms
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import Diagnosis, Feedback, SessionLocal, init_db  # noqa: E402
from app.features import FEATURES, feature_row  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "models" / "symptom_model.joblib"
MIN_ROWS = 150        # confirmed checks needed before training
MIN_PER_CLASS = 10    # faults seen fewer times than this are left out


def load_rows() -> tuple[pd.DataFrame, pd.Series]:
    init_db()
    X, y = [], []
    with SessionLocal() as db:
        rows = db.execute(
            select(Diagnosis, Feedback.confirmed_fault).join(Feedback, Feedback.diagnosis_id == Diagnosis.id)
            .where(Feedback.confirmed_fault.notin_(["other", "none"]))
        ).all()
    for diagnosis, fault in rows:
        X.append(feature_row(diagnosis.answers["symptoms"], diagnosis.result["service"], diagnosis.answers["bike"]["mileage_km"]))
        y.append(fault)
    return pd.DataFrame(X, columns=FEATURES), pd.Series(y, dtype="object")


def train(X: pd.DataFrame, y: pd.Series, min_rows: int = MIN_ROWS, min_per_class: int = MIN_PER_CLASS, out: Path = OUT) -> dict | None:
    counts = y.value_counts()
    keep = counts[counts >= min_per_class].index
    X, y = X[y.isin(keep)], y[y.isin(keep)]
    if len(y) < min_rows or len(keep) < 2:
        print(f"Not enough confirmed feedback yet: {len(y)} usable rows across {len(keep)} faults "
              f"(need {min_rows} rows, 2+ faults with {min_per_class}+ each). Nothing was trained.")
        return None
    model = RandomForestClassifier(n_estimators=200, min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1)
    folds = StratifiedKFold(n_splits=min(5, int(counts[keep].min())), shuffle=True, random_state=42)
    cv = cross_val_score(model, X, y, cv=folds, scoring="accuracy")
    model.fit(X, y)
    bundle = {
        "model": model, "features": FEATURES, "classes": list(model.classes_),
        "rows": int(len(y)), "cv_accuracy": round(float(cv.mean()), 4), "trained_on": str(date.today()),
    }
    out.parent.mkdir(exist_ok=True)
    joblib.dump(bundle, out, compress=3)
    print(f"Trained on {len(y)} confirmed checks, {len(keep)} faults. Cross-validated accuracy: {cv.mean():.3f}. Saved {out}")
    return bundle


if __name__ == "__main__":
    train(*load_rows())
