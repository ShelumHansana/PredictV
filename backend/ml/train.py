"""
PredictV - model training.

Trains the exhaust-gas "mixture condition" classifier on EngineFaultDB
(real laboratory measurements, see data/SOURCE.md) and writes:

    models/mixture_full.joblib    features: CO, HC, CO2, O2, Lambda
    models/mixture_basic.joblib   features: CO, HC
    models/metrics.json           every number shown in the app / README

Run from the project root:   npm run train   (or: python backend/ml/train.py)
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "raw" / "EngineFaultDB_Final.csv"
OUT = ROOT / "models"
SEED = 42

# Original dataset labels (EngineFaultDB, IEEE Access 2023)
ORIGINAL = {0: "no_fault", 1: "rich_mixture", 2: "lean_mixture", 3: "low_voltage"}

# Labels used by the app. "lean_mixture" and "low_voltage" are merged because
# they cannot be told apart from these measurements (see metrics.json ->
# four_class_check: the model is at coin-flip level between the two).
CLASSES = ["normal", "rich", "lean_or_ignition"]
MERGE = {0: 0, 1: 1, 2: 2, 3: 2}

FEATURE_SETS = {
    "full": ["CO", "HC", "CO2", "O2", "Lambda"],
    "basic": ["CO", "HC"],
}


def make_model() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=150, max_depth=12, min_samples_leaf=5,
        n_jobs=-1, random_state=SEED,
    )


def block_groups(y: pd.Series, blocks_per_class: int = 25) -> np.ndarray:
    """Consecutive rows of each class go into the same block.

    The rows are consecutive readings from engine runs, so neighbouring rows
    are almost identical. Keeping whole blocks together in one fold gives a
    stricter estimate than a random split.
    """
    groups = np.zeros(len(y), dtype=int)
    offset = 0
    for cls in sorted(y.unique()):
        idx = np.flatnonzero(y.values == cls)
        groups[idx] = offset + (np.arange(len(idx)) * blocks_per_class // len(idx))
        offset += blocks_per_class
    return groups


def evaluate(X: pd.DataFrame, y: pd.Series) -> dict:
    # 1) stratified random hold-out
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )
    m = make_model().fit(Xtr, ytr)
    p = m.predict(Xte)
    res = {
        "holdout_accuracy": round(float(accuracy_score(yte, p)), 4),
        "holdout_macro_f1": round(float(f1_score(yte, p, average="macro")), 4),
        "holdout_confusion_matrix": confusion_matrix(yte, p).tolist(),
        "holdout_test_rows": int(len(yte)),
    }
    # 2) blocked 5-fold cross-validation
    accs, f1s = [], []
    for tr, te in GroupKFold(n_splits=5).split(X, y, block_groups(y)):
        mm = make_model().fit(X.iloc[tr], y.iloc[tr])
        pp = mm.predict(X.iloc[te])
        accs.append(accuracy_score(y.iloc[te], pp))
        f1s.append(f1_score(y.iloc[te], pp, average="macro"))
    res["blocked_cv_accuracy_mean"] = round(float(np.mean(accs)), 4)
    res["blocked_cv_accuracy_std"] = round(float(np.std(accs)), 4)
    res["blocked_cv_macro_f1_mean"] = round(float(np.mean(f1s)), 4)
    return res


def main() -> None:
    OUT.mkdir(exist_ok=True)
    df = pd.read_csv(DATA)
    rows_raw = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    y4 = df["Fault"].astype(int)
    y3 = y4.map(MERGE)

    metrics: dict = {
        "trained_on": str(date.today()),
        "sklearn_version": sklearn.__version__,
        "dataset": {
            "name": "EngineFaultDB",
            "rows_raw": rows_raw,
            "rows_used": int(len(df)),
            "original_class_counts": {ORIGINAL[k]: int(v) for k, v in y4.value_counts().sort_index().items()},
            "app_class_counts": {CLASSES[k]: int(v) for k, v in y3.value_counts().sort_index().items()},
        },
        "classes": CLASSES,
        "models": {},
    }

    # Honest check: can the four original classes be separated?
    cols = FEATURE_SETS["full"]
    Xtr, Xte, ytr, yte = train_test_split(df[cols], y4, test_size=0.2, random_state=SEED, stratify=y4)
    p4 = make_model().fit(Xtr, ytr).predict(Xte)
    cm4 = confusion_matrix(yte, p4)
    metrics["four_class_check"] = {
        "accuracy": round(float(accuracy_score(yte, p4)), 4),
        "labels": [ORIGINAL[i] for i in range(4)],
        "confusion_matrix": cm4.tolist(),
        "lean_vs_low_voltage_accuracy": round(float((cm4[2, 2] + cm4[3, 3]) / cm4[2:, 2:].sum()), 4),
    }

    for name, cols in FEATURE_SETS.items():
        X = df[cols]
        res = evaluate(X, y3)
        res["features"] = cols
        # range the model has actually seen (used by the app to refuse
        # readings it knows nothing about)
        res["training_range"] = {
            c: [round(float(X[c].min()), 3), round(float(X[c].max()), 3)] for c in cols
        }
        final = make_model().fit(X, y3)
        res["feature_importance"] = {
            c: round(float(v), 4) for c, v in zip(cols, final.feature_importances_)
        }
        joblib.dump(final, OUT / f"mixture_{name}.joblib", compress=3)
        metrics["models"][name] = res
        print(f"[{name}] hold-out acc={res['holdout_accuracy']}  "
              f"blocked-CV acc={res['blocked_cv_accuracy_mean']} ± {res['blocked_cv_accuracy_std']}")

    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print("4-class check:", metrics["four_class_check"]["accuracy"],
          "| lean vs low-voltage:", metrics["four_class_check"]["lean_vs_low_voltage_accuracy"])
    print("Saved models and metrics to", OUT)


if __name__ == "__main__":
    main()
