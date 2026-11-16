"""Turns a rider's answers into the numeric row used by the learned symptom model.

Shared by the API (prediction) and ml/train_symptoms.py (training) so both
always build exactly the same columns.
"""

from __future__ import annotations

from typing import Optional

from app.knowledge import SERVICE_ITEMS, SYMPTOM_GROUPS

SYMPTOM_IDS = [s["id"] for g in SYMPTOM_GROUPS for s in g["symptoms"]]
SERVICE_SCORE = {"recent": 0.0, "due": 1.0, "overdue": 2.0, "unknown": -1.0}

FEATURES = (
    [f"sym_{s}" for s in SYMPTOM_IDS]
    + [f"svc_{i['id']}" for i in SERVICE_ITEMS]
    + ["mileage_km"]
)


def feature_row(symptoms: list[str], service: dict[str, str], mileage_km: Optional[float]) -> list[float]:
    chosen = set(symptoms)
    return (
        [1.0 if s in chosen else 0.0 for s in SYMPTOM_IDS]
        + [SERVICE_SCORE.get(service.get(i["id"], "unknown"), -1.0) for i in SERVICE_ITEMS]
        + [float(mileage_km) if mileage_km is not None else -1.0]
    )
