"""
ML Pipeline — the main orchestration layer for making predictions.

This module loads trained models and processes incoming emission data
to generate complete diagnostic predictions.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.ml.explainability import ExplainabilityEngine
from app.ml.feature_engine import FeatureEngineer
from app.ml.models.emission_classifier import EmissionClassifier
from app.ml.models.fault_detector import FaultDetector
from app.ml.models.forecaster import Forecaster
from app.ml.models.health_scorer import HealthScorer
from app.ml.models.rul_predictor import RULPredictor
from app.ml.preprocessor import DataPreprocessor
from app.ml.training import load_trained_models
from app.utils.constants import FAULT_SIGNATURES, REPAIR_COSTS, classify_health
from app.utils.helpers import clamp


class PredictionPipeline:
    """Loads trained models and runs complete diagnostic predictions."""

    def __init__(self, model_dir: str = "./ml_models"):
        self.model_dir = Path(model_dir)
        self.preprocessor: Optional[DataPreprocessor] = None
        self.feature_engineer: Optional[FeatureEngineer] = None
        self.health_scorer: Optional[HealthScorer] = None
        self.emission_classifier: Optional[EmissionClassifier] = None
        self.fault_detector: Optional[FaultDetector] = None
        self.rul_predictor: Optional[RULPredictor] = None
        self.forecaster: Optional[Forecaster] = None
        self.explainability: ExplainabilityEngine = ExplainabilityEngine()
        self.feature_names: List[str] = []
        self.is_loaded: bool = False

    def load_models(self) -> bool:
        """Load all trained models from disk."""
        try:
            models = load_trained_models(str(self.model_dir))
            self.preprocessor = models.get("preprocessor")
            self.feature_engineer = models.get("feature_engineer")
            self.health_scorer = models.get("health_scorer")
            self.emission_classifier = models.get("emission_classifier")
            self.fault_detector = models.get("fault_detector")
            self.rul_predictor = models.get("rul_predictor")
            self.forecaster = models.get("forecaster")
            self.feature_names = models.get("feature_names", [])

            # Setup explainability if health scorer is loaded
            if self.health_scorer and self.health_scorer.best_model:
                self.explainability.feature_names = self.feature_names

            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            self.is_loaded = False
            return False

    def predict(self, emission_data: Dict[str, Any], vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete diagnostic prediction pipeline."""
        if not self.is_loaded:
            return self._rule_based_prediction(emission_data, vehicle_data)

        try:
            # Prepare input data
            input_data = {**emission_data, **vehicle_data}
            df = pd.DataFrame([input_data])

            # Feature engineering
            if self.feature_engineer:
                df = self.feature_engineer.transform(df)

            # Get feature vector
            available_features = [f for f in self.feature_names if f in df.columns]
            missing_features = [f for f in self.feature_names if f not in df.columns]

            # Fill missing features with 0
            for f in missing_features:
                df[f] = 0.0

            X = df[self.feature_names].values.astype(np.float32)
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

            # Run all predictions
            result = {}

            # Health Score
            if self.health_scorer and self.health_scorer.is_trained:
                health_result = self.health_scorer.predict(X[0])
                result.update(health_result)
            else:
                result["health_score"] = self._estimate_health(emission_data)
                result["health_classification"] = classify_health(result["health_score"]).value
                result["confidence"] = 0.7

            # Emission Compliance
            fuel_type = vehicle_data.get("fuel_type", "petrol")
            if self.emission_classifier and self.emission_classifier.is_trained:
                emission_result = self.emission_classifier.predict(X[0], fuel_type)
                result["emission_compliance"] = emission_result["compliance"]
                result["emission_details"] = emission_result
            else:
                result["emission_compliance"] = self._estimate_compliance(emission_data, fuel_type)
                result["emission_details"] = {}

            # Fault Detection
            if self.fault_detector and self.fault_detector.is_trained:
                fault_result = self.fault_detector.predict(X[0])
                result["detected_faults"] = fault_result["detected_faults"]
                result["fault_count"] = fault_result["fault_count"]
                result["primary_fault"] = fault_result["primary_fault"]
                result["primary_fault_probability"] = fault_result["primary_fault_probability"]
            else:
                result["detected_faults"] = self._estimate_faults(emission_data)
                result["fault_count"] = len(result["detected_faults"])

            # RUL
            if self.rul_predictor and self.rul_predictor.is_trained:
                rul_result = self.rul_predictor.predict(X[0])
                result.update(rul_result)
            else:
                result.update(self._estimate_rul(result.get("health_score", 70), vehicle_data))

            # Forecasts
            health_score = result.get("health_score", 70)
            if self.forecaster and self.forecaster.is_trained:
                forecasts = self.forecaster.predict(X[0], current_health=health_score)
                result["forecasts"] = forecasts
            else:
                result["forecasts"] = self._estimate_forecasts(health_score)

            # Explainability
            shap_result = self.explainability.explain_shap(X[0])
            result["feature_importance"] = self.explainability.get_feature_importance(
                self.health_scorer.best_model
            ) if self.health_scorer and self.health_scorer.best_model else {}
            result["explanation_text"] = self.explainability.generate_explanation_text(
                shap_result,
                result.get("health_score", 70),
                [f["fault"] for f in result.get("detected_faults", [])[:5]],
            )

            # Derived insights
            result.update(self._compute_derived_insights(result))

            return result

        except Exception as e:
            print(f"ML prediction error: {e}")
            return self._rule_based_prediction(emission_data, vehicle_data)

    def _rule_based_prediction(self, emission_data: Dict, vehicle_data: Dict) -> Dict[str, Any]:
        """Fallback rule-based prediction when ML models are unavailable."""
        health = self._estimate_health(emission_data)
        fuel_type = vehicle_data.get("fuel_type", "petrol")
        compliance = self._estimate_compliance(emission_data, fuel_type)
        faults = self._estimate_faults(emission_data)
        rul = self._estimate_rul(health, vehicle_data)
        forecasts = self._estimate_forecasts(health)

        result = {
            "health_score": health,
            "health_classification": classify_health(health).value,
            "confidence": 0.65,
            "emission_compliance": compliance,
            "emission_details": {},
            "detected_faults": faults,
            "fault_count": len([f for f in faults if f["probability"] > 0.5]),
            "primary_fault": faults[0]["fault"] if faults else None,
            "primary_fault_probability": faults[0]["probability"] if faults else None,
            **rul,
            "forecasts": forecasts,
            "feature_importance": {},
            "explanation_text": f"Rule-based analysis: Health Score {health:.1f}/100",
        }
        result.update(self._compute_derived_insights(result))
        return result

    def _estimate_health(self, data: Dict) -> float:
        """Estimate health from emission values using engineering heuristics."""
        score = 100.0
        co = data.get("co_percent", 0.1)
        hc = data.get("hc_ppm", 50)
        nox = data.get("nox_ppm", 30)
        smoke = data.get("smoke_opacity", 5)
        lam = data.get("lambda_value", 1.0)
        cat_eff = data.get("catalytic_efficiency", 96)

        # Penalize high emissions
        if co > 0.3: score -= (co - 0.3) * 20
        if hc > 100: score -= (hc - 100) * 0.1
        if nox > 60: score -= (nox - 60) * 0.1
        if smoke > 10: score -= (smoke - 10) * 0.5
        if abs(lam - 1.0) > 0.05: score -= abs(lam - 1.0) * 40
        if cat_eff and cat_eff < 90: score -= (90 - cat_eff) * 1.5

        return round(clamp(score, 0, 100), 1)

    def _estimate_compliance(self, data: Dict, fuel_type: str) -> str:
        """Estimate compliance from emission limits."""
        is_diesel = fuel_type == "diesel"
        penalties = 0
        co = data.get("co_percent", 0.1)
        hc = data.get("hc_ppm", 50)
        nox = data.get("nox_ppm", 30)

        if co > (0.8 if is_diesel else 0.5): penalties += 2
        elif co > (0.5 if is_diesel else 0.3): penalties += 1
        if hc > (300 if is_diesel else 150): penalties += 2
        elif hc > (200 if is_diesel else 100): penalties += 1
        if nox > (150 if is_diesel else 100): penalties += 2
        elif nox > (80 if is_diesel else 60): penalties += 1

        if penalties >= 3: return "Fail"
        elif penalties >= 1: return "Warning"
        return "Pass"

    def _estimate_faults(self, data: Dict) -> List[Dict]:
        """Estimate faults from emission/sensor patterns."""
        faults = []
        co = data.get("co_percent", 0.1)
        hc = data.get("hc_ppm", 50)
        nox = data.get("nox_ppm", 30)
        lam = data.get("lambda_value", 1.0)
        cat_eff = data.get("catalytic_efficiency", 96)
        smoke = data.get("smoke_opacity", 5)
        coolant = data.get("coolant_temp", 90)
        maf = data.get("maf_sensor", 15)

        if co > 0.5 and lam < 0.97:
            faults.append({"fault": "Rich Fuel Mixture", "probability": min(0.9, co / 1.0),
                          "severity": "medium", "estimated_repair_cost": 200,
                          "description": "Excess fuel in the air-fuel mixture."})
        if nox > 80 and lam > 1.03:
            faults.append({"fault": "Lean Fuel Mixture", "probability": min(0.9, nox / 150),
                          "severity": "medium", "estimated_repair_cost": 200,
                          "description": "Insufficient fuel in the mixture."})
        if cat_eff and cat_eff < 85:
            faults.append({"fault": "Catalytic Converter Failure",
                          "probability": min(0.95, (90 - cat_eff) / 30),
                          "severity": "critical", "estimated_repair_cost": 1500,
                          "description": "Catalytic converter degradation detected."})
        if hc > 200:
            faults.append({"fault": "Engine Misfire", "probability": min(0.8, hc / 500),
                          "severity": "high", "estimated_repair_cost": 300,
                          "description": "Possible misfire causing high HC."})
        if maf and maf < 8:
            faults.append({"fault": "Dirty Air Filter", "probability": 0.7,
                          "severity": "low", "estimated_repair_cost": 50,
                          "description": "Restricted airflow detected."})
        if smoke > 20:
            faults.append({"fault": "Oil Burning", "probability": min(0.85, smoke / 40),
                          "severity": "high", "estimated_repair_cost": 1800,
                          "description": "Excessive smoke indicates oil burning."})
        if coolant and coolant > 105:
            faults.append({"fault": "Coolant Leakage", "probability": min(0.8, (coolant - 100) / 20),
                          "severity": "critical", "estimated_repair_cost": 800,
                          "description": "Elevated coolant temperature detected."})

        return sorted(faults, key=lambda x: x["probability"], reverse=True)

    def _estimate_rul(self, health: float, vehicle_data: Dict) -> Dict:
        """Estimate remaining useful life."""
        mileage = vehicle_data.get("mileage", 50000)
        remaining = max(0, (300000 - mileage) * (health / 100))
        return {
            "remaining_life_km": round(remaining),
            "km_to_maintenance": round(max(500, 15000 - (mileage % 15000) - (100 - health) * 50)),
            "km_to_major_repair": round(remaining * 0.5 if health < 50 else remaining * 0.7),
            "breakdown_probability": round(clamp((100 - health) / 150, 0, 0.95), 3),
        }

    def _estimate_forecasts(self, health: float) -> List[Dict]:
        """Estimate future forecasts."""
        forecasts = []
        for days in [30, 90, 180, 365]:
            deg = max(0, (100 - health) * 0.001 + 0.02) * days
            future = max(0, health - deg)
            drop = health - future
            forecasts.append({
                "horizon": f"{days}d" if days < 365 else "1y",
                "horizon_days": days,
                "health_score": round(future, 1),
                "risk_score": round(clamp((100 - future) / 100, 0, 1), 3),
                "engine_degradation_pct": round(drop, 1),
                "emission_increase_pct": round(drop * 0.5, 1),
                "fuel_efficiency_loss_pct": round(drop * 0.3, 1),
                "maintenance_cost": round(max(0, drop * 15), 0),
            })
        return forecasts

    def _compute_derived_insights(self, result: Dict) -> Dict:
        """Compute derived insights from prediction results."""
        health = result.get("health_score", 70)
        faults = result.get("detected_faults", [])

        # Repair costs
        total_min = sum(f.get("estimated_repair_cost", 0) * 0.6
                       for f in faults if f.get("probability", 0) > 0.5)
        total_max = sum(f.get("estimated_repair_cost", 0) * 1.5
                       for f in faults if f.get("probability", 0) > 0.5)

        # Risk and urgency
        if health < 30:
            risk = "Critical"
            urgency = "Critical"
        elif health < 50:
            risk = "High"
            urgency = "High"
        elif health < 70:
            risk = "Medium"
            urgency = "Medium"
        else:
            risk = "Low"
            urgency = "Low"

        # Fuel efficiency rating
        fuel_rating = clamp(health * 0.9 + 10, 0, 100)

        # Environmental impact (higher health = lower impact)
        env_impact = clamp(100 - health * 0.8, 0, 100)

        # Emission letter grade
        if health >= 90: grade = "A"
        elif health >= 75: grade = "B"
        elif health >= 60: grade = "C"
        elif health >= 40: grade = "D"
        else: grade = "F"

        # Recommendations
        recommendations = self._generate_recommendations(result)
        maintenance_schedule = self._generate_maintenance_schedule(result)

        return {
            "estimated_repair_cost_min": round(total_min, 2),
            "estimated_repair_cost_max": round(total_max, 2),
            "risk_level": risk,
            "urgency_level": urgency,
            "fuel_efficiency_rating": round(fuel_rating, 1),
            "environmental_impact_score": round(env_impact, 1),
            "emission_rating": grade,
            "recommendations": recommendations,
            "maintenance_schedule": maintenance_schedule,
            "overall_confidence": result.get("confidence", 0.7),
        }

    def _generate_recommendations(self, result: Dict) -> List[Dict]:
        """Generate actionable recommendations based on analysis."""
        recs = []
        health = result.get("health_score", 70)
        faults = result.get("detected_faults", [])
        compliance = result.get("emission_compliance", "Pass")

        if compliance == "Fail":
            recs.append({
                "title": "Urgent Emission Repair Required",
                "description": "Vehicle fails emission standards. Immediate repair needed before re-testing.",
                "priority": "Critical",
                "estimated_cost": 500,
            })

        for fault in faults[:5]:
            if fault.get("probability", 0) > 0.5:
                recs.append({
                    "title": f"Address {fault['fault']}",
                    "description": fault.get("description", ""),
                    "priority": fault.get("severity", "medium").title(),
                    "estimated_cost": fault.get("estimated_repair_cost", 200),
                })

        if health < 50:
            recs.append({
                "title": "Comprehensive Engine Inspection",
                "description": "Health score is below 50%. A full engine diagnostic is recommended.",
                "priority": "High",
                "estimated_cost": 200,
            })

        if not recs:
            recs.append({
                "title": "Continue Regular Maintenance",
                "description": "Engine is in good condition. Maintain regular service intervals.",
                "priority": "Low",
                "estimated_cost": 100,
            })

        return recs

    def _generate_maintenance_schedule(self, result: Dict) -> List[Dict]:
        """Generate a maintenance schedule based on predictions."""
        health = result.get("health_score", 70)
        km_to_maint = result.get("km_to_maintenance", 10000)

        schedule = [
            {
                "service": "Oil Change & Filter",
                "interval_km": 10000,
                "next_due_km": round(km_to_maint * 0.7),
                "priority": "Medium",
            },
            {
                "service": "Air Filter Replacement",
                "interval_km": 20000,
                "next_due_km": round(km_to_maint * 1.5),
                "priority": "Low",
            },
            {
                "service": "Spark Plug Replacement",
                "interval_km": 40000,
                "next_due_km": round(km_to_maint * 3),
                "priority": "Low",
            },
            {
                "service": "Full Engine Diagnostic",
                "interval_km": 50000,
                "next_due_km": round(km_to_maint * 4),
                "priority": "Medium" if health > 70 else "High",
            },
        ]

        if health < 50:
            schedule.insert(0, {
                "service": "Immediate Inspection Required",
                "interval_km": 0,
                "next_due_km": 0,
                "priority": "Critical",
            })

        return schedule
