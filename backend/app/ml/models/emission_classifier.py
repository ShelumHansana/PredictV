"""
Emission Compliance Classifier Model.

Predicts emission compliance status: Pass, Warning, or Fail.
Compares readings against legal emission limits (Euro 6 / EPA Tier 3).
"""

import warnings
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import cross_val_score

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
except ImportError:
    LGBMClassifier = None

try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None

from app.utils.constants import EMISSION_LIMITS, FuelType


class EmissionClassifier:
    """Classifies emission test results as Pass, Warning, or Fail."""

    def __init__(self):
        self.best_model: Optional[Any] = None
        self.best_model_name: str = ""
        self.all_models: Dict[str, Any] = {}
        self.model_scores: Dict[str, Dict[str, float]] = {}
        self.feature_names: List[str] = []
        self.label_map: Dict[int, str] = {0: "Pass", 1: "Warning", 2: "Fail"}
        self.reverse_label_map: Dict[str, int] = {"Pass": 0, "Warning": 1, "Fail": 2}
        self.is_trained: bool = False

    def _get_candidate_models(self) -> Dict[str, Any]:
        """Build candidate classifier models."""
        models = {
            "random_forest": RandomForestClassifier(
                n_estimators=200, max_depth=12, min_samples_split=5,
                random_state=42, n_jobs=-1, class_weight="balanced",
            ),
            "gradient_boosting": GradientBoostingClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, random_state=42,
            ),
        }

        if XGBClassifier is not None:
            models["xgboost"] = XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8, random_state=42,
                verbosity=0, eval_metric="mlogloss",
            )

        if LGBMClassifier is not None:
            models["lightgbm"] = LGBMClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8, random_state=42,
                verbose=-1, class_weight="balanced",
            )

        if CatBoostClassifier is not None:
            models["catboost"] = CatBoostClassifier(
                iterations=200, depth=6, learning_rate=0.1,
                random_state=42, verbose=0, auto_class_weights="Balanced",
            )

        return models

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
        cv_folds: int = 5,
    ) -> Dict[str, Dict[str, float]]:
        """Train all candidate models and select the best one."""
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        # Encode labels
        y_encoded = np.array([self.reverse_label_map.get(str(label), 0) for label in y])

        candidates = self._get_candidate_models()
        results = {}

        print("📊 Training Emission Compliance Classifier...")
        print(f"   Features: {X.shape[1]}, Samples: {X.shape[0]}")
        print(f"   Class distribution: {dict(zip(*np.unique(y_encoded, return_counts=True)))}")
        print()

        best_score = -np.inf
        for name, model in candidates.items():
            print(f"  Training {name}...", end=" ")
            try:
                cv_scores = cross_val_score(
                    model, X, y_encoded, cv=cv_folds, scoring="f1_weighted", n_jobs=-1
                )

                model.fit(X, y_encoded)
                y_pred = model.predict(X)

                metrics = {
                    "accuracy": float(accuracy_score(y_encoded, y_pred)),
                    "f1_weighted": float(f1_score(y_encoded, y_pred, average="weighted")),
                    "cv_f1_mean": float(cv_scores.mean()),
                    "cv_f1_std": float(cv_scores.std()),
                }
                results[name] = metrics
                self.all_models[name] = model

                print(f"Acc={metrics['accuracy']:.4f}, F1={metrics['f1_weighted']:.4f}, "
                      f"CV F1={metrics['cv_f1_mean']:.4f}")

                if metrics["cv_f1_mean"] > best_score:
                    best_score = metrics["cv_f1_mean"]
                    self.best_model = model
                    self.best_model_name = name

            except Exception as e:
                print(f"FAILED: {e}")
                results[name] = {"error": str(e)}

        self.model_scores = results
        self.is_trained = True
        print(f"\n  ✅ Best model: {self.best_model_name} (CV F1={best_score:.4f})")
        return results

    def predict(self, X: np.ndarray, fuel_type: str = "petrol") -> Dict[str, Any]:
        """Predict emission compliance with detailed breakdown."""
        if not self.is_trained or self.best_model is None:
            raise RuntimeError("Model not trained.")

        X_input = X.reshape(1, -1) if X.ndim == 1 else X
        pred_class = int(self.best_model.predict(X_input)[0])
        compliance = self.label_map[pred_class]

        # Get probabilities
        try:
            probs = self.best_model.predict_proba(X_input)[0]
            class_probs = {self.label_map[i]: round(float(p), 3) for i, p in enumerate(probs)}
        except Exception:
            class_probs = {compliance: 1.0}

        # Compare with legal limits
        limit_comparison = self._compare_with_limits(X, fuel_type)

        return {
            "compliance": compliance,
            "probabilities": class_probs,
            "confidence": round(max(class_probs.values()), 3),
            "limit_comparison": limit_comparison,
            "model_used": self.best_model_name,
        }

    def _compare_with_limits(self, X: np.ndarray, fuel_type: str) -> Dict[str, Any]:
        """Compare emission values against legal limits."""
        try:
            ft = FuelType(fuel_type)
        except ValueError:
            ft = FuelType.PETROL

        limits = EMISSION_LIMITS.get(ft, EMISSION_LIMITS[FuelType.PETROL])
        comparison = {}

        # Map feature indices to emission parameters
        emission_params = {
            "co_percent": None, "co2_percent": None, "hc_ppm": None,
            "o2_percent": None, "nox_ppm": None, "lambda_value": None,
            "smoke_opacity": None,
        }

        for i, fname in enumerate(self.feature_names):
            if fname in emission_params and i < len(X):
                value = float(X[i]) if X.ndim == 1 else float(X[0][i])
                emission_params[fname] = value

        for param, value in emission_params.items():
            if value is not None and param in limits:
                limit_info = limits[param]
                if "pass" in limit_info:
                    status = "Pass" if value <= limit_info["pass"] else (
                        "Warning" if value <= limit_info.get("warning", limit_info["pass"] * 1.5) else "Fail"
                    )
                    comparison[param] = {
                        "value": round(value, 3),
                        "limit": limit_info["pass"],
                        "status": status,
                        "unit": limit_info.get("unit", ""),
                    }

        return comparison

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the best model."""
        if not self.is_trained or self.best_model is None:
            return {}
        try:
            importances = self.best_model.feature_importances_
            return dict(sorted(
                zip(self.feature_names, importances), key=lambda x: x[1], reverse=True
            ))
        except AttributeError:
            return {}
