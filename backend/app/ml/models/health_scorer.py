"""
Engine Health Scorer Model.

Predicts engine health score (0-100) and classifies into categories:
Excellent, Good, Moderate, Poor, Critical.

Uses ensemble of Random Forest, XGBoost, LightGBM, CatBoost, and Gradient Boosting.
Automatically selects the best model via cross-validation.
"""

import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
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

from app.utils.constants import classify_health


class HealthScorer:
    """Predicts engine health score (0-100) using an auto-selected ensemble model."""

    def __init__(self):
        self.best_model: Optional[Any] = None
        self.best_model_name: str = ""
        self.all_models: Dict[str, Any] = {}
        self.model_scores: Dict[str, Dict[str, float]] = {}
        self.feature_names: List[str] = []
        self.is_trained: bool = False

    def _get_candidate_models(self) -> Dict[str, Any]:
        """Build dictionary of candidate models."""
        models = {
            "random_forest": RandomForestRegressor(
                n_estimators=200, max_depth=15, min_samples_split=5,
                min_samples_leaf=2, random_state=42, n_jobs=-1,
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, random_state=42,
            ),
        }

        if XGBRegressor is not None:
            models["xgboost"] = XGBRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8, random_state=42,
                verbosity=0,
            )

        if LGBMRegressor is not None:
            models["lightgbm"] = LGBMRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8, random_state=42,
                verbose=-1,
            )

        if CatBoostRegressor is not None:
            models["catboost"] = CatBoostRegressor(
                iterations=200, depth=6, learning_rate=0.1,
                random_state=42, verbose=0,
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
        candidates = self._get_candidate_models()
        results = {}

        print("🏥 Training Health Scorer Models...")
        print(f"   Features: {X.shape[1]}, Samples: {X.shape[0]}")
        print(f"   Target range: [{y.min():.1f}, {y.max():.1f}]")
        print()

        best_score = -np.inf
        for name, model in candidates.items():
            print(f"  Training {name}...", end=" ")
            try:
                # Cross-validation
                cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring="r2", n_jobs=-1)

                # Full fit
                model.fit(X, y)
                y_pred = model.predict(X)

                metrics = {
                    "r2": float(r2_score(y, y_pred)),
                    "mae": float(mean_absolute_error(y, y_pred)),
                    "rmse": float(np.sqrt(mean_squared_error(y, y_pred))),
                    "cv_r2_mean": float(cv_scores.mean()),
                    "cv_r2_std": float(cv_scores.std()),
                }
                results[name] = metrics
                self.all_models[name] = model

                print(f"R²={metrics['r2']:.4f}, MAE={metrics['mae']:.2f}, "
                      f"CV R²={metrics['cv_r2_mean']:.4f} ± {metrics['cv_r2_std']:.4f}")

                # Select best based on CV score
                if metrics["cv_r2_mean"] > best_score:
                    best_score = metrics["cv_r2_mean"]
                    self.best_model = model
                    self.best_model_name = name

            except Exception as e:
                print(f"FAILED: {e}")
                results[name] = {"error": str(e)}

        self.model_scores = results
        self.is_trained = True
        print(f"\n  ✅ Best model: {self.best_model_name} (CV R²={best_score:.4f})")
        return results

    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """Predict health score and classification for input features."""
        if not self.is_trained or self.best_model is None:
            raise RuntimeError("Model not trained. Call train() first.")

        raw_score = float(self.best_model.predict(X.reshape(1, -1) if X.ndim == 1 else X)[0])
        score = np.clip(raw_score, 0, 100)
        classification = classify_health(score)

        # Confidence based on model agreement
        predictions = []
        for name, model in self.all_models.items():
            try:
                pred = float(model.predict(X.reshape(1, -1) if X.ndim == 1 else X)[0])
                predictions.append(np.clip(pred, 0, 100))
            except Exception:
                pass

        if len(predictions) > 1:
            std_dev = np.std(predictions)
            confidence = max(0.5, 1 - std_dev / 30)  # Lower std = higher confidence
        else:
            confidence = 0.85

        return {
            "health_score": round(score, 1),
            "health_classification": classification.value,
            "confidence": round(confidence, 3),
            "model_used": self.best_model_name,
            "all_predictions": {name: round(np.clip(p, 0, 100), 1)
                                for name, p in zip(self.all_models.keys(), predictions)},
        }

    def predict_batch(self, X: np.ndarray) -> List[Dict[str, Any]]:
        """Predict health scores for a batch of inputs."""
        return [self.predict(X[i]) for i in range(X.shape[0])]

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the best model."""
        if not self.is_trained or self.best_model is None:
            return {}

        try:
            importances = self.best_model.feature_importances_
            importance_dict = dict(zip(self.feature_names, importances))
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        except AttributeError:
            return {}
