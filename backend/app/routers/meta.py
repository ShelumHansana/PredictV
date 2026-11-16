"""Questions, fault texts, limits and model facts the frontend needs to draw itself."""

from fastapi import APIRouter

from app.knowledge import FAULTS, ML_LABELS, SERVICE_ITEMS, SL_LIMITS, SYMPTOM_GROUPS
from app.services import mixture_model, symptom_model

router = APIRouter(prefix="/api", tags=["meta"])

_FAULT_FIELDS = ("en", "si", "what_en", "what_si", "fix_en", "fix_si", "who", "urgency")
_MODEL_FIELDS = ("features", "holdout_accuracy", "blocked_cv_accuracy_mean", "blocked_cv_accuracy_std", "training_range")


@router.get("/meta")
def meta() -> dict:
    m = mixture_model.metrics
    return {
        "symptom_groups": SYMPTOM_GROUPS,
        "service_items": SERVICE_ITEMS,
        "faults": {f["id"]: {k: f[k] for k in _FAULT_FIELDS} for f in FAULTS},
        "limits": SL_LIMITS,
        "ml_labels": ML_LABELS,
        "ml": {
            "ready": mixture_model.ready,
            "trained_on": m.get("trained_on"),
            "dataset": m.get("dataset"),
            "four_class_check": m.get("four_class_check"),
            "models": {name: {k: v[k] for k in _MODEL_FIELDS} for name, v in m.get("models", {}).items()},
            "symptom_model": (
                {k: symptom_model.bundle[k] for k in ("trained_on", "rows", "cv_accuracy", "classes")}
                if symptom_model.ready else None
            ),
        },
    }
