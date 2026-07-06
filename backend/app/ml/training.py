"""
ML Training Pipeline for PredictV.

Orchestrates the complete ML workflow:
1. Load & preprocess data
2. Engineer features
3. Train all model types
4. Evaluate & compare
5. Save best models
"""

import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from app.ml.feature_engine import FeatureEngineer
from app.ml.models.emission_classifier import EmissionClassifier
from app.ml.models.fault_detector import FaultDetector
from app.ml.models.forecaster import Forecaster
from app.ml.models.health_scorer import HealthScorer
from app.ml.models.rul_predictor import RULPredictor
from app.ml.preprocessor import DataPreprocessor
from app.utils.constants import FAULT_TYPES


class TrainingPipeline:
    """End-to-end ML training pipeline."""

    def __init__(self, data_path: str, model_dir: str = "./ml_models"):
        self.data_path = data_path
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()
        self.health_scorer = HealthScorer()
        self.emission_classifier = EmissionClassifier()
        self.fault_detector = FaultDetector()
        self.rul_predictor = RULPredictor()
        self.forecaster = Forecaster()

        self.training_results: Dict[str, Any] = {}
        self.feature_names: list = []

    def run(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """Execute the full training pipeline."""
        start_time = time.time()

        print("=" * 60)
        print("  PredictV ML Training Pipeline")
        print("=" * 60)
        print()

        # Step 1: Load data
        print("📂 Step 1: Loading data...")
        df = pd.read_csv(self.data_path)
        if sample_size and sample_size < len(df):
            df = df.sample(n=sample_size, random_state=42)
        print(f"   Loaded {len(df):,} records with {len(df.columns)} columns")
        print()

        # Step 2: Feature engineering
        print("🔧 Step 2: Feature engineering...")
        df = self.feature_engineer.transform(df)
        derived = self.feature_engineer.get_feature_names()
        print(f"   Added {len(derived)} derived features")
        print()

        # Step 3: Preprocess
        print("⚙️  Step 3: Preprocessing...")
        df_processed = self.preprocessor.fit_transform(df, normalize=False)
        print(f"   Processed {len(df_processed):,} records")
        print()

        # Step 4: Prepare feature matrix
        print("📊 Step 4: Preparing features...")
        feature_cols = self._get_feature_columns(df_processed)
        self.feature_names = feature_cols
        X = df_processed[feature_cols].values.astype(np.float32)
        # Replace any remaining NaN with 0
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        print(f"   Feature matrix shape: {X.shape}")
        print(f"   Features: {feature_cols[:5]}... ({len(feature_cols)} total)")
        print()

        # Step 5: Train Health Scorer
        print("─" * 60)
        y_health = df_processed["health_score"].values.astype(np.float32)
        health_results = self.health_scorer.train(X, y_health, feature_cols)
        self.training_results["health_scorer"] = health_results
        print()

        # Step 6: Train Emission Classifier
        print("─" * 60)
        y_compliance = df_processed["emission_compliance"].values
        emission_results = self.emission_classifier.train(X, y_compliance, feature_cols)
        self.training_results["emission_classifier"] = emission_results
        print()

        # Step 7: Train Fault Detector
        print("─" * 60)
        fault_cols = [f"fault_{f.lower().replace(' ', '_')}" for f in FAULT_TYPES]
        available_fault_cols = [c for c in fault_cols if c in df_processed.columns]
        if available_fault_cols:
            y_faults = df_processed[available_fault_cols].values.astype(np.int32)
            fault_results = self.fault_detector.train(X, y_faults, feature_cols)
            self.training_results["fault_detector"] = fault_results
        print()

        # Step 8: Train RUL Predictor
        print("─" * 60)
        rul_targets = {}
        for col in ["remaining_life_km", "km_to_maintenance", "km_to_major_repair", "breakdown_probability"]:
            if col in df_processed.columns:
                rul_targets[col] = df_processed[col].values.astype(np.float32)
        if rul_targets:
            rul_results = self.rul_predictor.train(X, rul_targets, feature_cols)
            self.training_results["rul_predictor"] = rul_results
        print()

        # Step 9: Train Forecaster
        print("─" * 60)
        forecast_targets = {}
        for col in df_processed.columns:
            if col.startswith("forecast_") and ("health" in col or "risk" in col):
                y_val = df_processed[col].values.astype(np.float32)
                y_val = np.nan_to_num(y_val, nan=0.0)
                forecast_targets[col] = y_val
        if forecast_targets:
            forecast_results = self.forecaster.train(X, forecast_targets, feature_cols)
            self.training_results["forecaster"] = forecast_results
        print()

        # Step 10: Save models
        print("─" * 60)
        print("💾 Saving models...")
        self._save_models()
        print()

        elapsed = time.time() - start_time
        print("=" * 60)
        print(f"  ✅ Training complete in {elapsed:.1f}s")
        print(f"  📁 Models saved to {self.model_dir}")
        print("=" * 60)

        return self.training_results

    def _get_feature_columns(self, df: pd.DataFrame) -> list:
        """Get all numeric feature columns (excluding target columns)."""
        exclude = {
            "health_score", "health_class", "emission_compliance",
            "fault_count", "active_faults", "fault_probabilities",
            "remaining_life_km", "km_to_maintenance", "km_to_major_repair",
            "breakdown_probability", "brand", "model", "climate",
            "driving_condition", "fuel_type",
        }
        # Also exclude forecast targets and fault binary columns
        exclude.update({c for c in df.columns if c.startswith("forecast_")})
        exclude.update({c for c in df.columns if c.startswith("fault_")})

        feature_cols = [
            c for c in df.columns
            if c not in exclude
            and df[c].dtype in [np.float64, np.float32, np.int64, np.int32, np.float16]
        ]
        return feature_cols

    def _save_models(self) -> None:
        """Save all trained models and preprocessors."""
        artifacts = {
            "preprocessor": self.preprocessor,
            "feature_engineer": self.feature_engineer,
            "health_scorer": self.health_scorer,
            "emission_classifier": self.emission_classifier,
            "fault_detector": self.fault_detector,
            "rul_predictor": self.rul_predictor,
            "forecaster": self.forecaster,
            "feature_names": self.feature_names,
        }
        for name, obj in artifacts.items():
            path = self.model_dir / f"{name}.pkl"
            with open(path, "wb") as f:
                pickle.dump(obj, f)
            print(f"   Saved {name} → {path}")

        # Save training results as JSON
        results_path = self.model_dir / "training_results.json"
        serializable = {}
        for key, value in self.training_results.items():
            serializable[key] = {
                k: {mk: mv for mk, mv in v.items() if isinstance(mv, (int, float, str))}
                if isinstance(v, dict) else str(v)
                for k, v in (value.items() if isinstance(value, dict) else {"result": value}.items())
            }
        with open(results_path, "w") as f:
            json.dump(serializable, f, indent=2, default=str)
        print(f"   Saved training_results.json")


def load_trained_models(model_dir: str = "./ml_models") -> Dict[str, Any]:
    """Load all trained models from disk."""
    model_path = Path(model_dir)
    models = {}

    model_files = [
        "preprocessor", "feature_engineer", "health_scorer",
        "emission_classifier", "fault_detector", "rul_predictor",
        "forecaster", "feature_names",
    ]

    for name in model_files:
        path = model_path / f"{name}.pkl"
        if path.exists():
            with open(path, "rb") as f:
                models[name] = pickle.load(f)

    return models


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train PredictV ML models")
    parser.add_argument("--data", type=str, default="./data/synthetic_vehicle_data.csv")
    parser.add_argument("--models", type=str, default="./ml_models")
    parser.add_argument("--sample", type=int, default=None, help="Use a subset for faster training")
    args = parser.parse_args()

    pipeline = TrainingPipeline(data_path=args.data, model_dir=args.models)
    pipeline.run(sample_size=args.sample)
