"""
PredictV diagnosis engine.

Three parts, kept separate on purpose so each can be explained:

1. MixtureModel  - machine learning. A RandomForest trained on EngineFaultDB
   reads exhaust-gas values and says: normal / rich / lean-or-ignition.
   Only used when the rider enters an emission test report.
2. diagnose()    - rule-based expert system over knowledge.FAULTS.
   The ML result (if any) is just one more piece of evidence.
3. SymptomModel  - machine learning, optional. Trained by ml/train_symptoms.py
   on diagnoses whose real cause a mechanic confirmed (the feedback riders
   leave in the app). It does not exist until enough feedback has been
   collected; when it does, it re-ranks the rule-based result.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd

from app.features import feature_row
from app.knowledge import FAULTS, SERVICE_ITEMS, SL_LIMITS

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
HIGH_MILEAGE_KM = 60_000
MIN_ML_CONFIDENCE = 0.60     # below this the ML result is shown but not used as evidence
LIKELY, POSSIBLE = 0.45, 0.22  # share of a fault's total evidence weight that was found
LIKELY_MIN_WEIGHT = 4          # ...and "likely" also needs at least this much evidence in total


class MixtureModel:
    """Loads the trained classifiers and refuses inputs outside what they were trained on."""

    def __init__(self, model_dir: Path = MODEL_DIR) -> None:
        self.metrics: dict[str, Any] = {}
        self.models: dict[str, Any] = {}
        try:
            self.metrics = json.loads((model_dir / "metrics.json").read_text())
            for name in self.metrics["models"]:
                self.models[name] = joblib.load(model_dir / f"mixture_{name}.joblib")
        except Exception as exc:  # models are optional - symptom diagnosis still works
            print(f"[WARN] ML models not loaded: {exc}")

    @property
    def ready(self) -> bool:
        return bool(self.models)

    def predict(self, readings: dict[str, Optional[float]]) -> Optional[dict[str, Any]]:
        if not self.ready:
            return None
        # use the 5-gas model when every value was given, otherwise CO + HC
        name = "full" if all(readings.get(c) is not None for c in self.metrics["models"]["full"]["features"]) else "basic"
        info = self.metrics["models"][name]
        cols = info["features"]
        if any(readings.get(c) is None for c in cols):
            return None

        outside = [
            c for c in cols
            if not (info["training_range"][c][0] <= readings[c] <= info["training_range"][c][1])
        ]
        base = {
            "model": name,
            "features_used": cols,
            "validation_accuracy": info["blocked_cv_accuracy_mean"],
        }
        if outside:
            return {**base, "status": "out_of_range", "outside": outside,
                    "training_range": {c: info["training_range"][c] for c in outside}}

        X = pd.DataFrame([[readings[c] for c in cols]], columns=cols)
        proba = self.models[name].predict_proba(X)[0]
        classes = self.metrics["classes"]
        best = int(proba.argmax())
        return {**base, "status": "ok", "label": classes[best],
                "confidence": round(float(proba[best]), 3),
                "probabilities": {c: round(float(p), 3) for c, p in zip(classes, proba)}}


class SymptomModel:
    """Fault classifier learned from mechanic-confirmed feedback (may be absent)."""

    def __init__(self, model_dir: Path = MODEL_DIR) -> None:
        self.bundle: Optional[dict[str, Any]] = None
        path = model_dir / "symptom_model.joblib"
        if path.exists():
            try:
                self.bundle = joblib.load(path)
            except Exception as exc:
                print(f"[WARN] Symptom model not loaded: {exc}")

    @property
    def ready(self) -> bool:
        return self.bundle is not None

    def probabilities(self, symptoms: list[str], service: dict[str, str], mileage_km: Optional[float]) -> dict[str, float]:
        if not self.bundle:
            return {}
        X = pd.DataFrame([feature_row(symptoms, service, mileage_km)], columns=self.bundle["features"])
        proba = self.bundle["model"].predict_proba(X)[0]
        return {c: float(p) for c, p in zip(self.bundle["classes"], proba)}


LEARNED_WEIGHT = 0.4   # share of the final ranking given to the learned model, when it exists


def service_state(item: dict, km_since: Optional[float]) -> str:
    if km_since is None:
        return "unknown"
    ok, overdue = item["limits_km"]
    return "recent" if km_since <= ok else ("due" if km_since <= overdue else "overdue")


def _observable(key: str, service: dict, emission: Optional[dict], mileage_km: Optional[float]) -> bool:
    if key.startswith("svc:"):
        return service.get(key.split(":")[1]) != "unknown"
    if key.startswith("gas:"):
        return emission is not None
    if key.startswith("ml:"):
        return emission is not None and bool(emission["ml"]) and emission["ml"]["status"] == "ok"
    if key == "high_mileage":
        return mileage_km is not None
    return True


def diagnose(
    symptoms: list[str],
    service_km: dict[str, Optional[float]],
    mileage_km: Optional[float],
    readings: dict[str, Optional[float]],
    model: MixtureModel,
    symptom_model: Optional[SymptomModel] = None,
) -> dict[str, Any]:
    evidence: set[str] = set(symptoms)

    service = {}
    for item in SERVICE_ITEMS:
        state = service_state(item, service_km.get(item["id"]))
        service[item["id"]] = state
        if state in ("due", "overdue"):
            evidence.add(f"svc:{item['id']}:{state}")

    if mileage_km is not None and mileage_km >= HIGH_MILEAGE_KM:
        evidence.add("high_mileage")

    # ── emission report (optional) ──────────────────────────────
    emission = None
    co, hc = readings.get("CO"), readings.get("HC")
    if co is not None and hc is not None:
        co_ok, hc_ok = co <= SL_LIMITS["co_percent"], hc <= SL_LIMITS["hc_ppm"]
        if not co_ok:
            evidence.add("gas:co_high")
        if not hc_ok:
            evidence.add("gas:hc_high")
        ml = model.predict(readings)
        if ml and ml["status"] == "ok" and ml["label"] != "normal" and ml["confidence"] >= MIN_ML_CONFIDENCE:
            evidence.add(f"ml:{ml['label']}")
        if ml and ml["status"] == "ok" and ml["label"] == "normal" and not (co_ok and hc_ok):
            ml["status"] = "conflict"  # over the legal limit: the limit check wins
        emission = {
            "co": {"value": co, "limit": SL_LIMITS["co_percent"], "pass": co_ok},
            "hc": {"value": hc, "limit": SL_LIMITS["hc_ppm"], "pass": hc_ok},
            "pass": co_ok and hc_ok,
            "ml": ml,
        }

    # ── score every fault ───────────────────────────────────────
    results = []
    for fault in FAULTS:
        found = {k: w for k, w in fault["evidence"].items() if k in evidence}
        # The ML reading alone never raises a fault: the model was trained on a
        # car engine, so it must be backed by something the rider reported.
        if not any(not k.startswith("ml:") for k in found):
            continue
        # Only count evidence that could have been observed with what the rider
        # entered; "due"/"overdue" of one item are alternatives, counted once.
        total = sum(w for k, w in fault["evidence"].items()
                    if not k.endswith(":due") and _observable(k, service, emission, mileage_km))
        score = min(1.0, sum(found.values()) / total)
        if score < POSSIBLE:
            continue
        results.append({
            "id": fault["id"],
            "score": round(score, 2),
            "level": "likely" if score >= LIKELY and sum(found.values()) >= LIKELY_MIN_WEIGHT else "possible",
            "reasons": sorted(found, key=lambda k: -found[k]),
            "who": fault["who"],
            "urgency": fault["urgency"],
        })
    # ── learned re-ranking (only once a symptom model has been trained) ──
    learned = symptom_model.probabilities(symptoms, service, mileage_km) if symptom_model and symptom_model.ready else {}
    for r in results:
        r["rank"] = r["score"]
        if learned:
            r["learned_probability"] = round(learned.get(r["id"], 0.0), 3)
            r["rank"] = (1 - LEARNED_WEIGHT) * r["score"] + LEARNED_WEIGHT * r["learned_probability"]
    results.sort(key=lambda r: -r["rank"])
    results = results[:5]
    for r in results:
        del r["rank"]

    # ── overall verdict ─────────────────────────────────────────
    likely = [r for r in results if r["level"] == "likely"]
    failed_test = emission is not None and not emission["pass"]
    if any(r["urgency"] == "high" for r in likely) or failed_test:
        overall = "fix_now"
    elif results:
        overall = "attention"
    else:
        overall = "ok"

    return {"overall": overall, "faults": results, "service": service, "emission": emission,
            "learned_model_used": bool(learned)}
