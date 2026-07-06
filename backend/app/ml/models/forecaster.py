"""
Forecaster Model.

Predicts future engine condition at 30, 90, 180, and 365-day horizons.
Forecasts: health degradation, emission increase, fuel efficiency loss,
maintenance cost, and risk score.
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


class Forecaster:
    """Forecasts future engine condition at multiple time horizons."""

    HORIZONS = [30, 90, 180, 365]
    FORECAST_TARGETS = ["health_score", "risk"]

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_names: Dict[str, str] = {}
        self.feature_names: List[str] = []
        self.is_trained: bool = False

    def _get_candidate_models(self) -> Dict[str, Any]:
        """Build candidate models."""
        models = {
            "random_forest": RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=42, n_jobs=-1,
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42,
            ),
        }
        if XGBRegressor is not None:
            models["xgboost"] = XGBRegressor(
                n_estimators=100, max_depth=5, learning_rate=0.1,
                random_state=42, verbosity=0,
            )
        if LGBMRegressor is not None:
            models["lightgbm"] = LGBMRegressor(
                n_estimators=100, max_depth=5, learning_rate=0.1,
                random_state=42, verbose=-1,
            )
        return models

    def train(
        self,
        X: np.ndarray,
        y_dict: Dict[str, np.ndarray],
        feature_names: Optional[List[str]] = None,
        cv_folds: int = 5,
    ) -> Dict[str, Dict[str, float]]:
        """Train forecast models for each horizon and target combination."""
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        all_results = {}

        print("🔮 Training Forecaster Models...")
        print(f"   Features: {X.shape[1]}, Samples: {X.shape[0]}")
        print()

        for target_key, y in y_dict.items():
            print(f"  📌 Target: {target_key}")
            candidates = self._get_candidate_models()
            best_score = -np.inf
            best_model = None
            best_name = ""

            for name, model in candidates.items():
                try:
                    cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring="r2", n_jobs=-1)
                    model.fit(X, y)
                    score = float(cv_scores.mean())
                    if score > best_score:
                        best_score = score
                        best_model = model
                        best_name = name
                except Exception:
                    continue

            if best_model is not None:
                self.models[target_key] = best_model
                self.model_names[target_key] = best_name
                print(f"     ✅ Best: {best_name} (CV R²={best_score:.4f})")
            print()

            all_results[target_key] = {"best_model": best_name, "cv_r2": best_score}

        self.is_trained = True
        return all_results

    def predict(self, X: np.ndarray, current_health: float = 75.0) -> List[Dict[str, Any]]:
        """Generate forecasts for all horizons."""
        if not self.is_trained:
            raise RuntimeError("Model not trained.")

        X_input = X.reshape(1, -1) if X.ndim == 1 else X
        forecasts = []

        for horizon in self.HORIZONS:
            forecast = {
                "horizon": f"{horizon}d" if horizon < 365 else "1y",
                "horizon_days": horizon,
            }

            # Predict health score at this horizon
            health_key = f"forecast_{horizon}d_health"
            risk_key = f"forecast_{horizon}d_risk"

            if health_key in self.models:
                future_health = float(np.clip(self.models[health_key].predict(X_input)[0], 0, 100))
            else:
                # Fallback: simple degradation model
                daily_deg = (100 - current_health) * 0.001 + 0.01
                future_health = max(0, current_health - daily_deg * horizon)
            forecast["health_score"] = round(future_health, 1)

            if risk_key in self.models:
                risk = float(np.clip(self.models[risk_key].predict(X_input)[0], 0, 1))
            else:
                risk = np.clip((100 - future_health) / 100, 0, 1)
            forecast["risk_score"] = round(risk, 3)

            # Derived forecasts
            health_drop = max(0, current_health - future_health)
            forecast["engine_degradation_pct"] = round(health_drop, 1)
            forecast["emission_increase_pct"] = round(health_drop * 0.5 + np.random.normal(0, 0.5), 1)
            forecast["fuel_efficiency_loss_pct"] = round(health_drop * 0.3 + np.random.normal(0, 0.3), 1)
            forecast["maintenance_cost"] = round(max(0, health_drop * 15 + np.random.normal(0, 10)), 0)

            forecasts.append(forecast)

        return forecasts

    def get_feature_importance(self) -> Dict[str, Dict[str, float]]:
        """Get feature importance for each forecast model."""
        importances = {}
        for target_key, model in self.models.items():
            try:
                imp = model.feature_importances_
                importances[target_key] = dict(sorted(
                    zip(self.feature_names, imp), key=lambda x: x[1], reverse=True
                ))
            except AttributeError:
                importances[target_key] = {}
        return importances
