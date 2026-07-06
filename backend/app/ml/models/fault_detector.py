"""
Fault Detector Model.

Multi-label classification for 21 possible engine faults.
Each fault gets an independent probability score.
"""

import warnings
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import f1_score, hamming_loss
from sklearn.model_selection import cross_val_score
from sklearn.multioutput import MultiOutputClassifier

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
except ImportError:
    LGBMClassifier = None

from app.utils.constants import FAULT_SIGNATURES, FAULT_TYPES


class FaultDetector:
    """Multi-label fault detection for 21 engine fault types."""

    FAULT_NAMES = FAULT_TYPES

    def __init__(self):
        self.best_model: Optional[Any] = None
        self.best_model_name: str = ""
        self.all_models: Dict[str, Any] = {}
        self.model_scores: Dict[str, Dict[str, float]] = {}
        self.feature_names: List[str] = []
        self.is_trained: bool = False

    def _get_candidate_models(self) -> Dict[str, Any]:
        """Build candidate multi-label models."""
        models = {
            "random_forest": MultiOutputClassifier(
                RandomForestClassifier(
                    n_estimators=150, max_depth=10, min_samples_split=5,
                    random_state=42, n_jobs=-1, class_weight="balanced",
                ),
                n_jobs=-1,
            ),
        }

        if XGBClassifier is not None:
            models["xgboost"] = MultiOutputClassifier(
                XGBClassifier(
                    n_estimators=150, max_depth=6, learning_rate=0.1,
                    subsample=0.8, random_state=42, verbosity=0,
                    eval_metric="logloss",
                ),
                n_jobs=-1,
            )

        if LGBMClassifier is not None:
            models["lightgbm"] = MultiOutputClassifier(
                LGBMClassifier(
                    n_estimators=150, max_depth=6, learning_rate=0.1,
                    subsample=0.8, random_state=42, verbose=-1,
                    class_weight="balanced",
                ),
                n_jobs=-1,
            )

        return models

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
        cv_folds: int = 3,
    ) -> Dict[str, Dict[str, float]]:
        """Train multi-label fault detection models."""
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        # y should be (n_samples, 21) binary matrix
        if y.ndim == 1:
            raise ValueError("y must be a 2D binary matrix with shape (n_samples, n_faults)")

        candidates = self._get_candidate_models()
        results = {}

        print("🔧 Training Fault Detector Models...")
        print(f"   Features: {X.shape[1]}, Samples: {X.shape[0]}, Fault types: {y.shape[1]}")
        print(f"   Fault prevalence: {y.mean(axis=0).round(3)[:5]}... (first 5)")
        print()

        best_score = -np.inf
        for name, model in candidates.items():
            print(f"  Training {name}...", end=" ")
            try:
                model.fit(X, y)
                y_pred = model.predict(X)

                # Metrics
                h_loss = float(hamming_loss(y, y_pred))
                f1_micro = float(f1_score(y, y_pred, average="micro"))
                f1_macro = float(f1_score(y, y_pred, average="macro"))

                metrics = {
                    "hamming_loss": h_loss,
                    "f1_micro": f1_micro,
                    "f1_macro": f1_macro,
                    "accuracy_per_label": float((y == y_pred).mean()),
                }
                results[name] = metrics
                self.all_models[name] = model

                print(f"F1_micro={f1_micro:.4f}, F1_macro={f1_macro:.4f}, "
                      f"Hamming={h_loss:.4f}")

                if f1_micro > best_score:
                    best_score = f1_micro
                    self.best_model = model
                    self.best_model_name = name

            except Exception as e:
                print(f"FAILED: {e}")
                results[name] = {"error": str(e)}

        self.model_scores = results
        self.is_trained = True
        print(f"\n  ✅ Best model: {self.best_model_name} (F1_micro={best_score:.4f})")
        return results

    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """Predict fault probabilities for all 21 fault types."""
        if not self.is_trained or self.best_model is None:
            raise RuntimeError("Model not trained.")

        X_input = X.reshape(1, -1) if X.ndim == 1 else X

        # Get binary predictions
        binary_preds = self.best_model.predict(X_input)[0]

        # Get probabilities from individual estimators
        probabilities = {}
        for i, estimator in enumerate(self.best_model.estimators_):
            fault_name = self.FAULT_NAMES[i] if i < len(self.FAULT_NAMES) else f"fault_{i}"
            try:
                prob = estimator.predict_proba(X_input)[0]
                # prob[1] is the probability of fault being present
                fault_prob = float(prob[1]) if len(prob) > 1 else float(binary_preds[i])
            except Exception:
                fault_prob = float(binary_preds[i])
            probabilities[fault_name] = round(fault_prob, 3)

        # Build fault list sorted by probability
        detected_faults = []
        for fault_name, prob in sorted(probabilities.items(), key=lambda x: x[1], reverse=True):
            if prob > 0.1:  # Only include faults with >10% probability
                severity = FAULT_SIGNATURES.get(fault_name, {}).get("severity", "medium")
                repair_cost = float(FAULT_SIGNATURES.get(fault_name, {}).get("avg_repair_cost", 300))
                detected_faults.append({
                    "fault": fault_name,
                    "probability": prob,
                    "severity": severity,
                    "estimated_repair_cost": repair_cost,
                    "description": self._get_fault_description(fault_name),
                })

        primary_fault = detected_faults[0] if detected_faults else None

        return {
            "detected_faults": detected_faults,
            "fault_count": sum(1 for f in detected_faults if f["probability"] > 0.5),
            "all_probabilities": probabilities,
            "primary_fault": primary_fault["fault"] if primary_fault else None,
            "primary_fault_probability": primary_fault["probability"] if primary_fault else None,
            "model_used": self.best_model_name,
        }

    def _get_fault_description(self, fault_name: str) -> str:
        """Get human-readable description for a fault."""
        descriptions = {
            "Dirty Air Filter": "Restricted airflow reducing engine efficiency and increasing emissions.",
            "Bad Spark Plug": "Worn or fouled spark plug causing incomplete combustion.",
            "Injector Problem": "Fuel injector malfunction leading to improper fuel delivery.",
            "Fuel Pump Issue": "Fuel pump delivering insufficient pressure for proper operation.",
            "Turbo Failure": "Turbocharger malfunction reducing boost pressure and power.",
            "Catalytic Converter Failure": "Catalytic converter unable to properly convert exhaust gases.",
            "Faulty Oxygen Sensor": "O₂ sensor providing incorrect readings to the ECU.",
            "Vacuum Leak": "Unmetered air entering the intake manifold.",
            "Poor Compression": "Reduced cylinder compression affecting power and efficiency.",
            "Engine Misfire": "One or more cylinders failing to fire consistently.",
            "Oil Burning": "Engine consuming oil due to worn seals or rings.",
            "Coolant Leakage": "Cooling system leak leading to potential overheating.",
            "Rich Fuel Mixture": "Excess fuel in the air-fuel mixture causing high CO.",
            "Lean Fuel Mixture": "Insufficient fuel causing high NOx and potential damage.",
            "EGR Failure": "EGR valve malfunction increasing NOx emissions.",
            "DPF Blockage": "Diesel particulate filter clogged, restricting exhaust flow.",
            "Valve Wear": "Worn intake or exhaust valves affecting sealing.",
            "Piston Ring Wear": "Worn piston rings allowing oil into combustion chamber.",
            "Head Gasket Issue": "Compromised head gasket allowing fluid mixing.",
            "Timing Problem": "Engine timing misalignment affecting combustion.",
            "Sensor Failure": "One or more engine sensors providing incorrect data.",
        }
        return descriptions.get(fault_name, "Engine fault detected requiring attention.")

    def get_feature_importance(self) -> Dict[str, float]:
        """Get average feature importance across all fault estimators."""
        if not self.is_trained or self.best_model is None:
            return {}

        try:
            importances = np.zeros(len(self.feature_names))
            for estimator in self.best_model.estimators_:
                importances += estimator.feature_importances_
            importances /= len(self.best_model.estimators_)
            return dict(sorted(
                zip(self.feature_names, importances), key=lambda x: x[1], reverse=True
            ))
        except AttributeError:
            return {}
