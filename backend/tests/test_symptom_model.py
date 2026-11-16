"""The learned model only exists once real feedback has been collected.
These tests use a handful of hand-written rows purely to exercise the code path."""

import pandas as pd

from app.engine import MixtureModel, SymptomModel, diagnose
from app.features import FEATURES, feature_row
from ml.train_symptoms import train

SERVICE = {"oil": "unknown", "air_filter": "unknown", "spark_plug": "unknown"}


def toy():
    rows, labels = [], []
    for _ in range(12):
        rows.append(feature_row(["weak_starter"], SERVICE, 30000)); labels.append("battery")
        rows.append(feature_row(["hard_start", "misfire"], SERVICE, 30000)); labels.append("ignition")
    return pd.DataFrame(rows, columns=FEATURES), pd.Series(labels, dtype="object")


def test_refuses_to_train_without_enough_data(tmp_path):
    X, y = toy()
    assert train(X, y, out=tmp_path / "m.joblib") is None and not (tmp_path / "m.joblib").exists()


def test_trained_model_reranks(tmp_path):
    X, y = toy()
    assert train(X, y, min_rows=20, min_per_class=5, out=tmp_path / "symptom_model.joblib")["rows"] == 24
    model = SymptomModel(tmp_path)
    assert model.ready
    # rules alone put spark_plug first; the learned data says "ignition" for these answers
    args = dict(symptoms=["hard_start", "misfire"], service_km={}, mileage_km=30000, readings={}, model=MixtureModel())
    assert diagnose(**args)["faults"][0]["id"] == "spark_plug"
    learned = diagnose(**args, symptom_model=model)
    assert learned["learned_model_used"] and learned["faults"][0]["id"] == "ignition"
