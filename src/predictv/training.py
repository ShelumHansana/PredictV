"""
PredictV Training Module (Petrol Motorbikes).

Trains all ML models on petrol motorbike data only: health scorer,
emission classifier, fault detector, RUL predictor, and forecaster.
Saves trained models to ml_models/.
"""

from __future__ import annotations

import json
import logging
import pickle
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    hamming_loss,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
except ImportError:
    xgb = None  # type: ignore[assignment]

try:
    import lightgbm as lgb
except ImportError:
    lgb = None  # type: ignore[assignment]

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
except ImportError:
    CatBoostClassifier = None  # type: ignore[assignment, misc]
    CatBoostRegressor = None  # type: ignore[assignment, misc]

from predictv.features import FeatureEngineer

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)

# ── Paths ────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data" / "raw"
MODEL_DIR = ROOT_DIR / "ml_models"
CONFIG_DIR = ROOT_DIR / "configs"

# ── Target columns ──────────────────────────────────────────
HEALTH_TARGET = "Engine_Health_Score"
EMISSION_TARGET = "Emission_Test"
FAULT_TARGETS = ["Maintenance_Required"]
RUL_TARGET = "Remaining_Useful_Life_months"

# ── Fault label columns (derived during preprocessing) ──────
FAULT_LABELS = [
    "fault_catalytic", "fault_o2_sensor", "fault_rich_mixture",
    "fault_lean_mixture", "fault_egr", "fault_ignition",
    "fault_cooling", "fault_exhaust_leak",
]


def load_dataset(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the raw emission dataset."""
    csv_path = path or DATA_DIR / "dataset.csv"
    logger.info("Loading dataset from %s", csv_path)
    df = pd.read_csv(csv_path)
    logger.info("Loaded %d rows × %d columns", len(df), len(df.columns))
    return df


def _derive_fault_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Derive binary fault labels from emission/sensor readings."""
    out = df.copy()
    out["fault_catalytic"] = (
        out.get("Catalytic_Converter", pd.Series(["Working"] * len(out))) != "Working"
    ).astype(int)
    out["fault_o2_sensor"] = (
        (out["O2_percent"] > 3.0) | (out["O2_percent"] < 0.1)
    ).astype(int)
    out["fault_rich_mixture"] = (
        (out["CO_percent"] > 1.5) & (out["Lambda"] < 0.97)
    ).astype(int)
    out["fault_lean_mixture"] = (
        (out["Lambda"] > 1.05) & (out["NOx_ppm"] > 150)
    ).astype(int)
    out["fault_egr"] = (out["NOx_ppm"] > 400).astype(int)
    out["fault_ignition"] = (out["HC_ppm"] > 400).astype(int)
    out["fault_cooling"] = (out["engine_temperature_C"] > 115).astype(int)
    out["fault_exhaust_leak"] = (
        (out["O2_percent"] > 3.0) & (out["CO_percent"] < 0.3)
    ).astype(int)
    return out


class Trainer:
    """
    Trains and evaluates all PredictV ML models on petrol motorbike data.

    Only petrol fuel-type records are used for training. Diesel and other
    fuel types are filtered out during data loading.

    Models trained:
        1. Health Scorer — regression (0–100 score)
        2. Emission Classifier — binary (Pass/Fail)
        3. Fault Detector — multi-label classification
        4. RUL Predictor — regression (remaining months)
        5. Forecaster — future health/risk projections
    """

    def __init__(
        self,
        data_path: Optional[Path] = None,
        model_dir: Optional[Path] = None,
    ) -> None:
        self.data_path = data_path or DATA_DIR / "dataset.csv"
        self.model_dir = model_dir or MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.feature_engineer = FeatureEngineer()
        self.scaler = StandardScaler()
        self.results: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        """Run the full training pipeline (petrol motorbikes only)."""
        logger.info("=" * 60)
        logger.info("PredictV Training Pipeline (Petrol Motorbikes)")
        logger.info("=" * 60)

        # 1. Load data
        raw_df = load_dataset(self.data_path)

        # 1b. Filter to petrol-only records
        if "fuel_type" in raw_df.columns:
            total_before = len(raw_df)
            raw_df = raw_df[raw_df["fuel_type"] == "Petrol"].reset_index(drop=True)
            logger.info(
                "Filtered to Petrol only: %d → %d rows (dropped %d non-petrol)",
                total_before, len(raw_df), total_before - len(raw_df),
            )
        else:
            logger.warning("No fuel_type column found — using all rows")

        # 2. Derive fault labels
        raw_df = _derive_fault_labels(raw_df)

        # 3. Separate targets before feature engineering
        targets: Dict[str, Any] = {}
        if HEALTH_TARGET in raw_df.columns:
            targets["health"] = raw_df[HEALTH_TARGET].copy()
        if EMISSION_TARGET in raw_df.columns:
            targets["emission"] = (
                (raw_df[EMISSION_TARGET] == "Fail").astype(int).copy()
            )
        if RUL_TARGET in raw_df.columns:
            targets["rul"] = raw_df[RUL_TARGET].copy()

        fault_cols = [c for c in FAULT_LABELS if c in raw_df.columns]
        if fault_cols:
            targets["faults"] = raw_df[fault_cols].copy()

        # 4. Feature engineering
        logger.info("Running feature engineering...")
        features_df = self.feature_engineer.fit_transform(raw_df)

        # Drop target columns from features
        drop_targets = [HEALTH_TARGET, EMISSION_TARGET, RUL_TARGET] + FAULT_LABELS
        feature_cols = [c for c in features_df.columns if c not in drop_targets]
        X = features_df[feature_cols]

        # 5. Scale features
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X), columns=X.columns, index=X.index
        )

        # 6. Train models
        if "health" in targets:
            self.results["health_scorer"] = self._train_health_scorer(
                X_scaled, targets["health"]
            )

        if "emission" in targets:
            self.results["emission_classifier"] = self._train_emission_classifier(
                X_scaled, targets["emission"]
            )

        if "faults" in targets:
            self.results["fault_detector"] = self._train_fault_detector(
                X_scaled, targets["faults"]
            )

        if "rul" in targets:
            self.results["rul_predictor"] = self._train_rul_predictor(
                X_scaled, targets["rul"]
            )

        # Forecaster (uses health + features)
        if "health" in targets:
            self.results["forecaster"] = self._train_forecaster(
                X_scaled, targets["health"]
            )

        # 7. Save artefacts
        self._save_feature_engineer()
        self._save_preprocessor()
        self._save_results()

        logger.info("=" * 60)
        logger.info("Training complete! Models saved to %s", self.model_dir)
        logger.info("=" * 60)

        return self.results

    # ── Health Scorer ────────────────────────────────────────

    def _train_health_scorer(
        self, X: pd.DataFrame, y: pd.Series
    ) -> Dict[str, Any]:
        """Train health score regression models."""
        logger.info("Training Health Scorer...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        models: Dict[str, Any] = {
            "random_forest": RandomForestRegressor(
                n_estimators=200, max_depth=15, random_state=42, n_jobs=-1
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42
            ),
        }
        if xgb is not None:
            models["xgboost"] = xgb.XGBRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42, verbosity=0,
            )
        if lgb is not None:
            models["lightgbm"] = lgb.LGBMRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42, verbose=-1,
            )
        if CatBoostRegressor is not None:
            models["catboost"] = CatBoostRegressor(
                iterations=200, depth=6, learning_rate=0.1,
                random_state=42, verbose=0,
            )

        results: Dict[str, Any] = {}
        best_score, best_model, best_name = -np.inf, None, ""

        for name, model in models.items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            r2 = r2_score(y_test, preds)
            mae = mean_absolute_error(y_test, preds)
            rmse = np.sqrt(mean_squared_error(y_test, preds))

            cv = cross_val_score(model, X, y, cv=5, scoring="r2", n_jobs=-1)

            results[name] = {
                "r2": r2, "mae": mae, "rmse": rmse,
                "cv_r2_mean": float(cv.mean()), "cv_r2_std": float(cv.std()),
            }
            logger.info(
                "  %s — R²=%.4f, MAE=%.4f, RMSE=%.4f", name, r2, mae, rmse
            )

            if cv.mean() > best_score:
                best_score, best_model, best_name = cv.mean(), model, name

        logger.info("  Best: %s (CV R²=%.4f)", best_name, best_score)
        self._save_model(best_model, "health_scorer.pkl")
        return results

    # ── Emission Classifier ──────────────────────────────────

    def _train_emission_classifier(
        self, X: pd.DataFrame, y: pd.Series
    ) -> Dict[str, Any]:
        """Train emission pass/fail classifier."""
        logger.info("Training Emission Classifier...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        models: Dict[str, Any] = {
            "random_forest": RandomForestClassifier(
                n_estimators=200, max_depth=15, random_state=42, n_jobs=-1
            ),
            "gradient_boosting": GradientBoostingClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42
            ),
        }
        if xgb is not None:
            models["xgboost"] = xgb.XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42, verbosity=0,
                use_label_encoder=False, eval_metric="logloss",
            )
        if lgb is not None:
            models["lightgbm"] = lgb.LGBMClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42, verbose=-1,
            )
        if CatBoostClassifier is not None:
            models["catboost"] = CatBoostClassifier(
                iterations=200, depth=6, learning_rate=0.1,
                random_state=42, verbose=0,
            )

        results: Dict[str, Any] = {}
        best_score, best_model, best_name = -np.inf, None, ""

        for name, model in models.items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            acc = accuracy_score(y_test, preds)
            f1 = f1_score(y_test, preds, average="weighted")

            cv = cross_val_score(
                model, X, y, cv=5, scoring="f1_weighted", n_jobs=-1
            )

            results[name] = {
                "accuracy": acc, "f1_weighted": f1,
                "cv_f1_mean": float(cv.mean()), "cv_f1_std": float(cv.std()),
            }
            logger.info("  %s — Acc=%.4f, F1=%.4f", name, acc, f1)

            if cv.mean() > best_score:
                best_score, best_model, best_name = cv.mean(), model, name

        logger.info("  Best: %s (CV F1=%.4f)", best_name, best_score)
        self._save_model(best_model, "emission_classifier.pkl")
        return results

    # ── Fault Detector ───────────────────────────────────────

    def _train_fault_detector(
        self, X: pd.DataFrame, y: pd.DataFrame
    ) -> Dict[str, Any]:
        """Train multi-label fault detector."""
        logger.info("Training Fault Detector...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        models: Dict[str, Any] = {
            "random_forest": MultiOutputClassifier(
                RandomForestClassifier(
                    n_estimators=200, max_depth=15, random_state=42, n_jobs=-1
                )
            ),
        }
        if xgb is not None:
            models["xgboost"] = MultiOutputClassifier(
                xgb.XGBClassifier(
                    n_estimators=200, max_depth=6, learning_rate=0.1,
                    random_state=42, verbosity=0,
                    use_label_encoder=False, eval_metric="logloss",
                )
            )
        if lgb is not None:
            models["lightgbm"] = MultiOutputClassifier(
                lgb.LGBMClassifier(
                    n_estimators=200, max_depth=6, learning_rate=0.1,
                    random_state=42, verbose=-1,
                )
            )

        results: Dict[str, Any] = {}
        best_score, best_model, best_name = np.inf, None, ""

        for name, model in models.items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            hl = hamming_loss(y_test, preds)
            f1_micro = f1_score(y_test, preds, average="micro")
            f1_macro = f1_score(y_test, preds, average="macro")
            acc_per_label = np.mean(
                np.array([
                    accuracy_score(y_test.iloc[:, i], preds[:, i])
                    for i in range(y_test.shape[1])
                ])
            )

            results[name] = {
                "hamming_loss": hl, "f1_micro": f1_micro,
                "f1_macro": f1_macro, "accuracy_per_label": acc_per_label,
            }
            logger.info(
                "  %s — Hamming=%.4f, F1-micro=%.4f", name, hl, f1_micro
            )

            if hl < best_score:
                best_score, best_model, best_name = hl, model, name

        logger.info("  Best: %s (Hamming=%.4f)", best_name, best_score)
        self._save_model(best_model, "fault_detector.pkl")
        return results

    # ── RUL Predictor ────────────────────────────────────────

    def _train_rul_predictor(
        self, X: pd.DataFrame, y: pd.Series
    ) -> Dict[str, Any]:
        """Train remaining useful life regression models."""
        logger.info("Training RUL Predictor...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        models: Dict[str, Any] = {}
        if xgb is not None:
            models["xgboost"] = xgb.XGBRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42, verbosity=0,
            )
        if lgb is not None:
            models["lightgbm"] = lgb.LGBMRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42, verbose=-1,
            )

        if not models:
            models["gradient_boosting"] = GradientBoostingRegressor(
                n_estimators=200, max_depth=6, random_state=42
            )

        results: Dict[str, Any] = {}
        best_score, best_model, best_name = -np.inf, None, ""

        for name, model in models.items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            r2 = r2_score(y_test, preds)
            mae = mean_absolute_error(y_test, preds)

            results[name] = {"r2": r2, "mae": mae}
            logger.info("  %s — R²=%.4f, MAE=%.4f", name, r2, mae)

            if r2 > best_score:
                best_score, best_model, best_name = r2, model, name

        logger.info("  Best: %s (R²=%.4f)", best_name, best_score)
        self._save_model(best_model, "rul_predictor.pkl")
        return results

    # ── Forecaster ───────────────────────────────────────────

    def _train_forecaster(
        self, X: pd.DataFrame, health: pd.Series
    ) -> Dict[str, Any]:
        """Train forecasting models for future health/risk at various horizons."""
        logger.info("Training Forecaster...")
        results: Dict[str, Any] = {}

        horizons = [30, 90, 180, 365]
        best_models: Dict[str, Any] = {}

        for days in horizons:
            # Simulate future health as degraded version of current
            decay = 1.0 - (days / 365) * 0.05  # ~5% annual degradation baseline
            noise = pd.Series(
                np.random.RandomState(42 + days).normal(0, 1.5, len(health)).tolist(),
                index=health.index,
            )
            future_health = (health * decay + noise).clip(0, 100)

            future_risk = 100 - future_health

            for target_name, target in [
                (f"forecast_{days}d_health", future_health),
                (f"forecast_{days}d_risk", future_risk),
            ]:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, target, test_size=0.2, random_state=42
                )

                candidates: Dict[str, Any] = {}
                if lgb is not None:
                    candidates["lightgbm"] = lgb.LGBMRegressor(
                        n_estimators=150, max_depth=5, learning_rate=0.1,
                        random_state=42, verbose=-1,
                    )
                if xgb is not None:
                    candidates["xgboost"] = xgb.XGBRegressor(
                        n_estimators=150, max_depth=5, learning_rate=0.1,
                        random_state=42, verbosity=0,
                    )
                if not candidates:
                    candidates["gradient_boosting"] = GradientBoostingRegressor(
                        n_estimators=150, max_depth=5, random_state=42
                    )

                best_cv, best_m_name = -np.inf, ""
                for m_name, m in candidates.items():
                    cv = cross_val_score(
                        m, X, target, cv=5, scoring="r2", n_jobs=-1
                    )
                    if cv.mean() > best_cv:
                        best_cv, best_m_name = cv.mean(), m_name

                results[target_name] = {
                    "best_model": best_m_name,
                    "cv_r2": float(best_cv),
                }

                # Train best on full data
                best_candidate = candidates[best_m_name]
                best_candidate.fit(X, target)
                best_models[target_name] = best_candidate

        # Save all forecast models as one dict
        self._save_model(best_models, "forecaster.pkl")
        return results

    # ── Persistence ──────────────────────────────────────────

    def _save_model(self, model: Any, filename: str) -> None:
        """Save a trained model to disk."""
        path = self.model_dir / filename
        with open(path, "wb") as f:
            pickle.dump(model, f)
        logger.info("Saved %s (%.1f KB)", filename, path.stat().st_size / 1024)

    def _save_feature_engineer(self) -> None:
        """Save the fitted feature engineer."""
        path = self.model_dir / "feature_engineer.pkl"
        with open(path, "wb") as f:
            pickle.dump(self.feature_engineer, f)

        path2 = self.model_dir / "feature_names.pkl"
        with open(path2, "wb") as f:
            pickle.dump(self.feature_engineer.get_feature_names(), f)
        logger.info("Saved feature_engineer.pkl and feature_names.pkl")

    def _save_preprocessor(self) -> None:
        """Save the fitted scaler."""
        path = self.model_dir / "preprocessor.pkl"
        with open(path, "wb") as f:
            pickle.dump(self.scaler, f)
        logger.info("Saved preprocessor.pkl")

    def _save_results(self) -> None:
        """Save training results as JSON."""
        path = self.model_dir / "training_results.json"

        # Convert any numpy values
        def _convert(obj: Any) -> Any:
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        with open(path, "w") as f:
            json.dump(self.results, f, indent=2, default=_convert)
        logger.info("Saved training_results.json")
