"""
Remaining Useful Life (RUL) Predictor Model.

Estimates:
- Remaining engine life (km)
- Distance to next maintenance
- Distance to major repair
- Probability of breakdown
"""

import warnings
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None

try:
    from lightgbm import LGBMRegressor
except ImportError:
    LGBMRegressor = None

try:
    from catboost import CatBoostRegressor
except ImportError:
    CatBoostRegressor = None


class RULPredictor:
    """Predicts remaining useful life metrics for the engine."""

    TARGET_NAMES = [
        "remaining_life_km",
        "km_to_maintenance",
        "km_to_major_repair",
        "breakdown_probability",
    ]

    def __init__(self):
        self.models: Dict[str, Any] = {}  # One model per target
        self.model_names: Dict[str, str] = {}
        self.feature_names: List[str] = []
        self.is_trained: bool = False

    def _get_candidate_models(self) -> Dict[str, Any]:
        """Build candidate regression models."""
        models = {
            "random_forest": RandomForestRegressor(
                n_estimators=150, max_depth=12, random_state=42, n_jobs=-1,
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42,
            ),
        }
        if XGBRegressor is not None:
            models["xgboost"] = XGBRegressor(
                n_estimators=150, max_depth=6, learning_rate=0.1,
                random_state=42, verbosity=0,
            )
        if LGBMRegressor is not None:
            models["lightgbm"] = LGBMRegressor(
                n_estimators=150, max_depth=6, learning_rate=0.1,
                random_state=42, verbose=-1,
            )
        if CatBoostRegressor is not None:
            models["catboost"] = CatBoostRegressor(
                iterations=150, depth=6, learning_rate=0.1,
                random_state=42, verbose=0,
            )
        return models

    def train(
        self,
        X: np.ndarray,
        y_dict: Dict[str, np.ndarray],
        feature_names: Optional[List[str]] = None,
        cv_folds: int = 5,
    ) -> Dict[str, Dict[str, float]]:
        """Train separate models for each RUL target."""
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        all_results = {}

        print("⏳ Training RUL Predictor Models...")
        print(f"   Features: {X.shape[1]}, Samples: {X.shape[0]}")
        print()

        for target_name in self.TARGET_NAMES:
            if target_name not in y_dict:
                print(f"  ⚠ Skipping {target_name} — not in training data")
                continue

            y = y_dict[target_name]
            print(f"  📌 Target: {target_name}")
            print(f"     Range: [{y.min():.1f}, {y.max():.1f}], Mean: {y.mean():.1f}")

            candidates = self._get_candidate_models()
            best_score = -np.inf
            best_model = None
            best_name = ""
            target_results = {}

            for name, model in candidates.items():
                try:
                    cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring="r2", n_jobs=-1)
                    model.fit(X, y)
                    y_pred = model.predict(X)

                    metrics = {
                        "r2": float(r2_score(y, y_pred)),
                        "mae": float(mean_absolute_error(y, y_pred)),
                        "cv_r2_mean": float(cv_scores.mean()),
                    }
                    target_results[name] = metrics

                    if metrics["cv_r2_mean"] > best_score:
                        best_score = metrics["cv_r2_mean"]
                        best_model = model
                        best_name = name

                except Exception as e:
                    target_results[name] = {"error": str(e)}

            if best_model is not None:
                self.models[target_name] = best_model
                self.model_names[target_name] = best_name
                print(f"     ✅ Best: {best_name} (CV R²={best_score:.4f})")

            all_results[target_name] = target_results
            print()

        self.is_trained = True
        return all_results

    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """Predict all RUL metrics."""
        if not self.is_trained:
            raise RuntimeError("Model not trained.")

        X_input = X.reshape(1, -1) if X.ndim == 1 else X
        results = {}

        for target_name, model in self.models.items():
            try:
                pred = float(model.predict(X_input)[0])
                if target_name == "breakdown_probability":
                    pred = np.clip(pred, 0, 1)
                else:
                    pred = max(0, pred)
                results[target_name] = round(pred, 1)
            except Exception:
                results[target_name] = None

        return {
            "remaining_life_km": results.get("remaining_life_km"),
            "km_to_maintenance": results.get("km_to_maintenance"),
            "km_to_major_repair": results.get("km_to_major_repair"),
            "breakdown_probability": results.get("breakdown_probability"),
            "models_used": self.model_names,
        }

    def get_feature_importance(self) -> Dict[str, Dict[str, float]]:
        """Get feature importance for each target model."""
        importances = {}
        for target_name, model in self.models.items():
            try:
                imp = model.feature_importances_
                importances[target_name] = dict(sorted(
                    zip(self.feature_names, imp), key=lambda x: x[1], reverse=True
                ))
            except AttributeError:
                importances[target_name] = {}
        return importances
