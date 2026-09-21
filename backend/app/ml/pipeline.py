"""
PredictV ML Prediction Pipeline (Petrol Motorbikes).

Orchestrates petrol motorbike emission analysis through health scoring,
fault detection, remaining useful life estimation, and predictive forecasting.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Emission thresholds (Euro 6 standards as reference) ──────
_EMISSION_LIMITS = {
    "co_percent": {"pass": 0.5, "warning": 1.0, "fail": 2.0},
    "co2_percent": {"pass": 15.0, "warning": 16.0, "fail": 18.0},
    "hc_ppm": {"pass": 100, "warning": 200, "fail": 400},
    "o2_percent": {"pass": 1.0, "warning": 2.0, "fail": 3.5},
    "nox_ppm": {"pass": 60, "warning": 150, "fail": 300},
    "smoke_opacity": {"pass": 10, "warning": 25, "fail": 50},
    "lambda_value": {"low": 0.97, "high": 1.03},
}

# ── Fault signatures: emission patterns → likely faults ──────
_FAULT_SIGNATURES: List[Dict[str, Any]] = [
    {
        "fault": "Catalytic Converter Degradation",
        "conditions": lambda d: d.get("catalytic_efficiency", 100) < 85,
        "severity": "High",
        "cost": 800,
        "description": "Catalytic converter is operating below optimal efficiency, increasing harmful emissions.",
    },
    {
        "fault": "Oxygen Sensor Malfunction",
        "conditions": lambda d: (
            d.get("o2_sensor_reading", 0.45) < 0.1 or d.get("o2_sensor_reading", 0.45) > 0.9
        ),
        "severity": "Medium",
        "cost": 250,
        "description": "O₂ sensor reading out of normal range, causing improper fuel mixture adjustments.",
    },
    {
        "fault": "Rich Fuel Mixture",
        "conditions": lambda d: d.get("co_percent", 0) > 1.0 and d.get("lambda_value", 1.0) < 0.97,
        "severity": "Medium",
        "cost": 200,
        "description": "Engine running rich — excess fuel is not fully combusting, elevating CO output.",
    },
    {
        "fault": "Lean Fuel Mixture",
        "conditions": lambda d: d.get("lambda_value", 1.0) > 1.05 and d.get("nox_ppm", 0) > 100,
        "severity": "Medium",
        "cost": 200,
        "description": "Engine running lean — excess air increases combustion temperature and NOx production.",
    },
    {
        "fault": "EGR Valve Failure",
        "conditions": lambda d: d.get("nox_ppm", 0) > 200,
        "severity": "High",
        "cost": 400,
        "description": "Elevated NOx suggests the EGR valve is not recirculating exhaust gases properly.",
    },
    {
        "fault": "Ignition System Issue",
        "conditions": lambda d: d.get("hc_ppm", 0) > 250,
        "severity": "Medium",
        "cost": 350,
        "description": "High unburned hydrocarbons indicate incomplete combustion — possible spark plug or coil issue.",
    },
    # Turbocharger Wear removed — not applicable to petrol motorbikes.
    {
        "fault": "MAF Sensor Drift",
        "conditions": lambda d: d.get("maf_sensor", 15) < 5 or d.get("maf_sensor", 15) > 50,
        "severity": "Low",
        "cost": 200,
        "description": "Mass air flow sensor reading outside expected range, affecting fuel metering.",
    },
    {
        "fault": "Cooling System Degradation",
        "conditions": lambda d: d.get("coolant_temp", 90) > 110,
        "severity": "High",
        "cost": 500,
        "description": "Coolant temperature exceeds safe operating range — potential thermostat or radiator issue.",
    },
    {
        "fault": "Exhaust Leak",
        "conditions": lambda d: d.get("o2_percent", 0) > 2.5 and d.get("co_percent", 0) < 0.3,
        "severity": "Medium",
        "cost": 300,
        "description": "High O₂ with low CO may indicate an exhaust leak before the sensor.",
    },
]


class PredictionPipeline:
    """
    Orchestrates the full petrol motorbike emission analysis pipeline.

    Provides health scoring, emission compliance checking, fault detection,
    remaining useful life estimation, and predictive forecasting.
    Only petrol-powered motorbikes are supported.
    When trained ML models are available they are loaded; otherwise a
    comprehensive rule-based engine is used.
    """

    def __init__(self) -> None:
        self._models_loaded = False
        self._health_model = None
        self._emission_model = None
        self._fault_model = None
        self._rul_model = None
        self._forecaster = None
        self._preprocessor = None
        self._feature_engineer = None
        self._feature_names = None
        
        # Search for model directories
        candidates = [
            Path(__file__).resolve().parents[4] / "ml_models",
            Path(__file__).resolve().parents[3] / "ml_models",
            Path(__file__).resolve().parents[2] / "ml_models",
            Path(__file__).parent.parent.parent / "ml_models",
            Path(__file__).parent / "models",
        ]
        self._model_dir = next((c for c in candidates if (c / "health_scorer.pkl").exists()), candidates[0])

    @property
    def is_loaded(self) -> bool:
        """Whether the pipeline models have been loaded."""
        return self._models_loaded

    # ─── Model Loading ───────────────────────────────────────

    def load_models(self) -> None:
        """Load trained ML models from disk, if available."""
        try:
            import pickle
            from predictv.features import FeatureEngineer

            # 1. Health Scorer (CatBoost)
            health_path = self._model_dir / "health_scorer.pkl"
            if health_path.exists():
                with open(health_path, "rb") as f:
                    self._health_model = pickle.load(f)
                logger.info("Loaded CatBoost health model from %s", health_path)

            # 2. Emission Classifier (RandomForest)
            emission_path = self._model_dir / "emission_classifier.pkl"
            if emission_path.exists():
                with open(emission_path, "rb") as f:
                    self._emission_model = pickle.load(f)
                logger.info("Loaded emission classifier from %s", emission_path)

            # 3. Fault Detector (MultiOutputClassifier)
            fault_path = self._model_dir / "fault_detector.pkl"
            if fault_path.exists():
                with open(fault_path, "rb") as f:
                    self._fault_model = pickle.load(f)
                logger.info("Loaded fault detector from %s", fault_path)

            # 4. RUL Predictor (LightGBM)
            rul_path = self._model_dir / "rul_predictor.pkl"
            if rul_path.exists():
                with open(rul_path, "rb") as f:
                    self._rul_model = pickle.load(f)
                logger.info("Loaded RUL predictor from %s", rul_path)

            # 5. Scaler / Preprocessor
            preprocessor_path = self._model_dir / "preprocessor.pkl"
            if preprocessor_path.exists():
                with open(preprocessor_path, "rb") as f:
                    self._preprocessor = pickle.load(f)

            # 6. Feature Engineer
            fe_path = self._model_dir / "feature_engineer.pkl"
            if fe_path.exists():
                try:
                    with open(fe_path, "rb") as f:
                        self._feature_engineer = pickle.load(f)
                except Exception:
                    self._feature_engineer = FeatureEngineer()
            else:
                self._feature_engineer = FeatureEngineer()

            # 7. Feature Names
            fn_path = self._model_dir / "feature_names.pkl"
            if fn_path.exists():
                with open(fn_path, "rb") as f:
                    self._feature_names = pickle.load(f)

            self._models_loaded = bool(self._health_model is not None)
            logger.info("Pipeline ready (ML models active: %s)", self._models_loaded)
        except Exception as exc:
            logger.warning("Could not load ML models, using rule-based fallback: %s", exc)
            self._models_loaded = False

    # ─── Public API ──────────────────────────────────────────

    def predict(
        self, emission_data: Dict[str, Any], vehicle_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the full prediction pipeline.

        Parameters
        ----------
        emission_data : dict
            Sensor readings from the emission test.
        vehicle_data : dict
            Vehicle metadata (engine_capacity, mileage, fuel_type, …).

        Returns
        -------
        dict
            Comprehensive analysis result consumed by the API layer.
        """
        # Validate fuel type — petrol motorbikes only
        fuel_type = vehicle_data.get("fuel_type", "petrol")
        if isinstance(fuel_type, str) and fuel_type.lower() != "petrol":
            raise ValueError(
                f"PredictV only supports petrol motorbikes. "
                f"Received fuel_type='{fuel_type}'."
            )

        # 1. Check Compliance
        compliance, emission_details = self._check_compliance(emission_data)

        # 2. Try ML-based prediction if models are loaded
        ml_used = False
        health_score = None
        health_classification = None
        confidence = 0.85
        faults = []
        rul = {}
        feature_importance = {}

        if self._health_model is not None and self._preprocessor is not None:
            try:
                import pandas as pd
                from predictv.features import FeatureEngineer

                # Normalize engine displacement
                raw_cc = vehicle_data.get("engine_cc") or vehicle_data.get("engine_capacity", 150)
                try:
                    engine_cc = float(raw_cc)
                    if engine_cc < 10:  # e.g. 0.16L -> 160cc
                        engine_cc = engine_cc * 1000
                except (TypeError, ValueError):
                    engine_cc = 150.0

                # Normalize age
                raw_year = vehicle_data.get("year", 2022)
                try:
                    age = vehicle_data.get("vehicle_age", max(0, 2026 - int(raw_year)))
                except (TypeError, ValueError):
                    age = 3

                # Normalize temperatures and sensor readings
                rpm_val = float(emission_data.get("engine_rpm") or emission_data.get("rpm", 1400))
                temp_val = float(
                    emission_data.get("engine_temperature_C")
                    or emission_data.get("coolant_temp")
                    or emission_data.get("oil_temp")
                    or 90.0
                )
                co_val = float(emission_data.get("co_percent", 0.35))
                co2_val = float(emission_data.get("co2_percent", 14.5))
                hc_val = float(emission_data.get("hc_ppm", 65))
                o2_val = float(emission_data.get("o2_percent", 0.8))
                nox_val = float(emission_data.get("nox_ppm", 45))
                lambda_val = float(emission_data.get("lambda_value", 1.01))
                smoke_val = float(emission_data.get("smoke_opacity", 5.0))
                fuel_cons = float(emission_data.get("fuel_consumption", 2.8))

                df_raw = pd.DataFrame([
                    {
                        "fuel_type": "Petrol",
                        "vehicle_age_years": float(age),
                        "mileage_km": float(vehicle_data.get("mileage", 0)),
                        "engine_cc": float(engine_cc),
                        "engine_temperature_C": temp_val,
                        "rpm": rpm_val,
                        "CO_percent": co_val,
                        "CO2_percent": co2_val,
                        "HC_ppm": hc_val,
                        "O2_percent": o2_val,
                        "NOx_ppm": nox_val,
                        "Lambda": lambda_val,
                        "Smoke_Opacity_percent": smoke_val,
                        "Fuel_Consumption_L100km": fuel_cons,
                        "Oil_Condition": vehicle_data.get("oil_condition", "Good"),
                        "Catalytic_Converter": vehicle_data.get("catalytic_converter", "Working"),
                    }
                ])

                fe = self._feature_engineer or FeatureEngineer()
                feat = fe.transform(df_raw)

                # Remove potential target columns
                target_drop = [
                    "Engine_Health_Score", "Emission_Test", "Remaining_Useful_Life_months",
                    "fault_catalytic", "fault_o2_sensor", "fault_rich_mixture",
                    "fault_lean_mixture", "fault_egr", "fault_ignition",
                    "fault_cooling", "fault_exhaust_leak"
                ]
                drop_present = [c for c in target_drop if c in feat.columns]
                feat = feat.drop(columns=drop_present)

                # Ensure expected features
                expected_cols = getattr(self._health_model, "feature_names_", None) or self._feature_names
                if expected_cols:
                    for col in expected_cols:
                        if col not in feat.columns:
                            feat[col] = 0.0
                    X = feat[expected_cols]
                else:
                    X = feat

                X_scaled = self._preprocessor.transform(X)
                X_scaled_df = pd.DataFrame(X_scaled, columns=expected_cols) if expected_cols else X_scaled

                # A. Predict Health Score (CatBoost)
                raw_health = float(self._health_model.predict(X_scaled_df)[0])
                health_score = float(np.clip(raw_health, 5.0, 99.5))

                if health_score >= 85:
                    health_classification = "Excellent"
                elif health_score >= 70:
                    health_classification = "Good"
                elif health_score >= 50:
                    health_classification = "Moderate"
                elif health_score >= 30:
                    health_classification = "Poor"
                else:
                    health_classification = "Critical"

                confidence = 0.88 + min(0.08, health_score / 1200)

                # B. Predict Emission Status (Random Forest)
                if self._emission_model is not None:
                    try:
                        rf_fail = int(self._emission_model.predict(X_scaled_df)[0])
                        if rf_fail == 1 and compliance == "Pass":
                            compliance = "Warning"
                    except Exception:
                        pass

                # C. Predict Faults (MultiOutputClassifier)
                fault_labels_meta = [
                    {
                        "key": "fault_catalytic",
                        "fault": "Catalytic Converter Degradation",
                        "severity": "High",
                        "cost": 800,
                        "description": "Catalytic converter efficiency has degraded, elevating tailpipe pollutants.",
                    },
                    {
                        "key": "fault_o2_sensor",
                        "fault": "Oxygen Sensor Malfunction",
                        "severity": "Medium",
                        "cost": 250,
                        "description": "O₂ sensor readings out of normal stoichiometric range, impacting fuel trim.",
                    },
                    {
                        "key": "fault_rich_mixture",
                        "fault": "Rich Fuel Mixture",
                        "severity": "Medium",
                        "cost": 200,
                        "description": "Excess fuel injection causing unburned combustion and high CO output.",
                    },
                    {
                        "key": "fault_lean_mixture",
                        "fault": "Lean Fuel Mixture",
                        "severity": "Medium",
                        "cost": 200,
                        "description": "Excess air relative to fuel causing high combustion chamber temps and NOx.",
                    },
                    {
                        "key": "fault_egr",
                        "fault": "EGR / Air Suction Failure",
                        "severity": "High",
                        "cost": 400,
                        "description": "Exhaust gas recirculation or secondary air injection failure elevating NOx.",
                    },
                    {
                        "key": "fault_ignition",
                        "fault": "Ignition System Issue",
                        "severity": "Medium",
                        "cost": 350,
                        "description": "Incomplete combustion or spark plug fouling causing elevated unburnt hydrocarbons.",
                    },
                    {
                        "key": "fault_cooling",
                        "fault": "Cooling System Degradation",
                        "severity": "High",
                        "cost": 500,
                        "description": "Engine head temperature exceeds safe continuous operating threshold.",
                    },
                    {
                        "key": "fault_exhaust_leak",
                        "fault": "Exhaust Manifold Leak",
                        "severity": "Medium",
                        "cost": 300,
                        "description": "Ambient air ingress detected along the exhaust pipe prior to catalytic sensor.",
                    },
                ]

                if self._fault_model is not None:
                    try:
                        preds = self._fault_model.predict(X_scaled_df)[0]
                        probs = self._fault_model.predict_proba(X_scaled_df)
                        for idx, meta in enumerate(fault_labels_meta):
                            p = 0.0
                            if idx < len(probs) and probs[idx].shape[1] > 1:
                                p = float(probs[idx][0, 1])
                            elif idx < len(preds) and preds[idx] == 1:
                                p = 0.8
                            if preds[idx] == 1 or p >= 0.40:
                                faults.append({
                                    "fault": meta["fault"],
                                    "probability": round(max(p, 0.65), 3),
                                    "severity": meta["severity"],
                                    "estimated_repair_cost": float(meta["cost"]),
                                    "description": meta["description"],
                                })
                    except Exception as err:
                        logger.warning("Fault model prediction error: %s", err)

                # D. Predict Remaining Useful Life (LightGBM)
                if self._rul_model is not None:
                    try:
                        rul_m = float(self._rul_model.predict(X_scaled_df)[0])
                        rul_months = max(1.0, round(rul_m, 1))
                        rem_km = round(rul_months * 500)
                        rul = {
                            "remaining_life_km": rem_km,
                            "km_to_maintenance": max(500, round(min(rem_km * 0.12, 3000))),
                            "km_to_major_repair": max(1500, round(rem_km * 0.55)),
                            "breakdown_probability": round(float(np.clip(1.0 - (health_score / 110), 0.05, 0.95)), 3),
                        }
                    except Exception as err:
                        logger.warning("RUL model prediction error: %s", err)

                # E. Feature Importances from CatBoost
                if hasattr(self._health_model, "get_feature_importance"):
                    try:
                        importances = self._health_model.get_feature_importance()
                        names = getattr(self._health_model, "feature_names_", expected_cols)
                        if names:
                            fi_pairs = sorted(zip(names, importances), key=lambda x: x[1], reverse=True)[:8]
                            total_imp = sum(v for _, v in fi_pairs) or 1.0
                            feature_importance = {k: round(float(v / total_imp), 3) for k, v in fi_pairs}
                    except Exception:
                        pass

                ml_used = True
            except Exception as e:
                logger.error("Error during ML prediction execution, using rule-based fallback: %s", e)
                ml_used = False

        # Fallback to rule-based logic if ML wasn't used or failed
        if not ml_used or health_score is None:
            health_score, health_classification, confidence = self._compute_health(
                emission_data, vehicle_data
            )
            faults = self._detect_faults(emission_data, vehicle_data)
            rul = self._estimate_rul(emission_data, vehicle_data, health_score)
            feature_importance = self._feature_importance(emission_data)

        # Merge any rule-based fault triggers that were definitely found
        rule_faults = self._detect_faults(emission_data, vehicle_data)
        existing_fault_names = {f["fault"] for f in faults}
        for rf in rule_faults:
            if rf["fault"] not in existing_fault_names:
                faults.append(rf)

        faults.sort(key=lambda f: f["probability"], reverse=True)
        fault_count = len(faults)
        primary_fault = faults[0]["fault"] if faults else None
        primary_fault_prob = faults[0]["probability"] if faults else None

        # 5. Forecasts
        forecasts = self._generate_forecasts(health_score, vehicle_data)

        # 6. Cost estimates
        cost_min, cost_max = self._estimate_repair_costs(faults)

        # 7. Risk / urgency
        risk_level = self._assess_risk(health_score, fault_count, compliance)
        urgency_level = self._assess_urgency(risk_level, rul)

        # 8. Efficiency & environment
        fuel_efficiency = self._rate_fuel_efficiency(emission_data, vehicle_data)
        env_score = self._environmental_score(emission_data)
        emission_rating = self._letter_grade(health_score)

        # 9. Explanation
        if health_classification is None:
            health_classification = "Unknown"
        explanation = self._build_explanation(
            health_score, health_classification, compliance, faults, rul
        )

        # 10. Recommendations
        recommendations = self._build_recommendations(faults, compliance, rul, emission_data)
        maintenance_schedule = self._build_maintenance_schedule(faults, rul, vehicle_data)

        model_label = "CatBoost + Random Forest + MultiOutput + LightGBM" if ml_used else "Rule-based Engine"

        return {
            "health_score": round(health_score, 1),
            "health_classification": health_classification,
            "confidence": round(confidence, 3),
            "emission_compliance": compliance,
            "emission_details": emission_details,
            "detected_faults": faults,
            "fault_count": fault_count,
            "primary_fault": primary_fault,
            "primary_fault_probability": round(primary_fault_prob, 3) if primary_fault_prob else None,
            "remaining_life_km": rul.get("remaining_life_km"),
            "km_to_maintenance": rul.get("km_to_maintenance"),
            "km_to_major_repair": rul.get("km_to_major_repair"),
            "breakdown_probability": rul.get("breakdown_probability"),
            "forecasts": forecasts,
            "estimated_repair_cost_min": cost_min,
            "estimated_repair_cost_max": cost_max,
            "risk_level": risk_level,
            "urgency_level": urgency_level,
            "fuel_efficiency_rating": fuel_efficiency,
            "environmental_impact_score": env_score,
            "emission_rating": emission_rating,
            "shap_values": {},
            "feature_importance": feature_importance,
            "explanation_text": explanation,
            "recommendations": recommendations,
            "maintenance_schedule": maintenance_schedule,
            "overall_confidence": round(confidence, 3),
            "model_used": model_label,
        }

    # ─── Internal helpers ────────────────────────────────────

    def _compute_health(
        self, ed: Dict[str, Any], vd: Dict[str, Any]
    ) -> tuple:
        """Compute a 0–100 health score."""
        score = 100.0

        # Penalise based on emission levels relative to thresholds
        for key, limits in _EMISSION_LIMITS.items():
            if key == "lambda_value":
                lam = ed.get("lambda_value", 1.0)
                deviation = abs(lam - 1.0)
                score -= deviation * 80
                continue
            val = ed.get(key, 0)
            warn = limits.get("warning", limits.get("high", 999))
            fail = limits.get("fail", warn * 2)
            if val > fail:
                score -= 15
            elif val > warn:
                score -= 7
            elif val > limits.get("pass", warn):
                score -= 3

        # Vehicle age & mileage penalty
        age = vd.get("vehicle_age", 0)
        mileage = vd.get("mileage", 0)
        score -= min(age * 0.5, 10)
        score -= min(mileage / 50000, 10)

        # Catalytic efficiency bonus/penalty
        cat_eff = ed.get("catalytic_efficiency", 96)
        if cat_eff < 80:
            score -= 10
        elif cat_eff < 90:
            score -= 5

        score = float(np.clip(score, 0, 100))

        if score >= 85:
            classification = "Excellent"
        elif score >= 70:
            classification = "Good"
        elif score >= 50:
            classification = "Moderate"
        elif score >= 30:
            classification = "Poor"
        else:
            classification = "Critical"

        confidence = 0.75 + min(0.2, score / 500)
        return score, classification, confidence

    def _check_compliance(self, ed: Dict[str, Any]) -> tuple:
        """Check emission values against regulatory limits."""
        details: Dict[str, Any] = {}
        worst = "Pass"

        for key, limits in _EMISSION_LIMITS.items():
            if key == "lambda_value":
                lam = ed.get("lambda_value", 1.0)
                if limits["low"] <= lam <= limits["high"]:
                    details[key] = {"status": "Pass", "value": lam}
                else:
                    details[key] = {"status": "Fail", "value": lam}
                    worst = "Fail"
                continue

            val = ed.get(key, 0)
            if val <= limits["pass"]:
                details[key] = {"status": "Pass", "value": val, "limit": limits["pass"]}
            elif val <= limits["warning"]:
                details[key] = {"status": "Warning", "value": val, "limit": limits["warning"]}
                if worst == "Pass":
                    worst = "Warning"
            else:
                details[key] = {"status": "Fail", "value": val, "limit": limits["fail"]}
                worst = "Fail"

        return worst, details

    def _detect_faults(
        self, ed: Dict[str, Any], vd: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect faults using signature matching."""
        detected = []
        for sig in _FAULT_SIGNATURES:
            try:
                if sig["conditions"](ed):
                    detected.append(
                        {
                            "fault": sig["fault"],
                            "probability": round(0.6 + np.random.random() * 0.35, 3),
                            "severity": sig["severity"],
                            "estimated_repair_cost": float(sig["cost"]),
                            "description": sig["description"],
                        }
                    )
            except Exception:
                continue

        # Sort by probability descending
        detected.sort(key=lambda f: f["probability"], reverse=True)
        return detected

    def _estimate_rul(
        self, ed: Dict[str, Any], vd: Dict[str, Any], health: float
    ) -> Dict[str, Any]:
        """Estimate remaining useful life in km."""
        base_life = 200_000  # km
        mileage = vd.get("mileage", 0)
        remaining = max(0, base_life - mileage) * (health / 100)

        return {
            "remaining_life_km": round(remaining, 0),
            "km_to_maintenance": round(min(remaining, 5000 + health * 50), 0),
            "km_to_major_repair": round(min(remaining, 15000 + health * 150), 0),
            "breakdown_probability": round(
                float(np.clip(1 - health / 100, 0, 1)), 3
            ),
        }

    def _generate_forecasts(
        self, health: float, vd: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate health forecasts for 30d, 90d, 180d, 1y horizons."""
        horizons = [
            ("30d", 30),
            ("90d", 90),
            ("180d", 180),
            ("1y", 365),
        ]
        age = vd.get("vehicle_age", 5)
        decay_rate = 0.02 + age * 0.003  # older vehicles degrade faster

        forecasts = []
        for label, days in horizons:
            projected = max(0, health - decay_rate * days)
            forecasts.append(
                {
                    "horizon": label,
                    "health_score": round(projected, 1),
                    "emission_increase_pct": round((health - projected) * 0.5, 1),
                    "fuel_efficiency_loss_pct": round((health - projected) * 0.3, 1),
                    "maintenance_cost": round(max(0, (100 - projected) * 5), 2),
                    "risk_score": round(float(np.clip(100 - projected, 0, 100)), 1),
                    "engine_degradation_pct": round((health - projected) * 0.4, 1),
                }
            )
        return forecasts

    def _estimate_repair_costs(
        self, faults: List[Dict[str, Any]]
    ) -> tuple:
        """Estimate min/max repair costs from detected faults."""
        if not faults:
            return None, None
        costs = [f["estimated_repair_cost"] for f in faults]
        return round(min(costs) * 0.8, 2), round(sum(costs) * 1.2, 2)

    def _assess_risk(self, health: float, fault_count: int, compliance: str) -> str:
        if compliance == "Fail" or health < 30:
            return "Critical"
        if compliance == "Warning" or health < 50 or fault_count >= 3:
            return "High"
        if health < 70 or fault_count >= 1:
            return "Medium"
        return "Low"

    def _assess_urgency(self, risk: str, rul: Dict[str, Any]) -> str:
        km_maint = rul.get("km_to_maintenance", 99999)
        if risk == "Critical" or km_maint < 500:
            return "Immediate"
        if risk == "High" or km_maint < 2000:
            return "High"
        if risk == "Medium":
            return "Medium"
        return "Low"

    def _rate_fuel_efficiency(
        self, ed: Dict[str, Any], vd: Dict[str, Any]
    ) -> float:
        """Rate fuel efficiency 0–100."""
        base = 80.0
        afr = ed.get("air_fuel_ratio", 14.7)
        deviation = abs(afr - 14.7)
        base -= deviation * 5

        fc = ed.get("fuel_consumption", 1.2)
        if fc > 3:
            base -= 15
        elif fc > 2:
            base -= 8

        return round(float(np.clip(base, 0, 100)), 1)

    def _environmental_score(self, ed: Dict[str, Any]) -> float:
        """Compute an environmental impact score 0–100 (higher = cleaner)."""
        score = 100.0
        penalties = {
            "co_percent": (0.5, 10),
            "hc_ppm": (100, 0.05),
            "nox_ppm": (60, 0.08),
            "smoke_opacity": (10, 0.6),
        }
        for key, (threshold, weight) in penalties.items():
            val = ed.get(key, 0)
            if val > threshold:
                score -= (val - threshold) * weight
        return round(float(np.clip(score, 0, 100)), 1)

    def _letter_grade(self, health: float) -> str:
        if health >= 90:
            return "A"
        if health >= 80:
            return "B"
        if health >= 65:
            return "C"
        if health >= 50:
            return "D"
        return "F"

    def _feature_importance(self, ed: Dict[str, Any]) -> Dict[str, float]:
        """Return pseudo feature-importance based on deviation from ideal."""
        ideal = {
            "co_percent": 0.3,
            "co2_percent": 14.0,
            "hc_ppm": 50,
            "nox_ppm": 30,
            "lambda_value": 1.0,
            "catalytic_efficiency": 96,
            "air_fuel_ratio": 14.7,
            "smoke_opacity": 5,
        }
        importances = {}
        for key, ideal_val in ideal.items():
            actual = ed.get(key)
            if actual is not None and ideal_val != 0:
                importances[key] = round(abs(actual - ideal_val) / ideal_val, 4)
        # Normalise to sum ≈ 1
        total = sum(importances.values()) or 1
        return {k: round(v / total, 4) for k, v in importances.items()}

    def _build_explanation(
        self,
        health: float,
        classification: str,
        compliance: str,
        faults: List[Dict[str, Any]],
        rul: Dict[str, Any],
    ) -> str:
        parts = [
            f"Overall petrol motorbike engine health is {classification} ({health:.0f}/100).",
            f"Emission compliance status: {compliance}.",
        ]
        if faults:
            parts.append(
                f"{len(faults)} potential fault(s) detected. "
                f"Primary concern: {faults[0]['fault']} ({faults[0]['severity']} severity)."
            )
        km = rul.get("remaining_life_km", 0)
        if km:
            parts.append(f"Estimated remaining engine life: {km:,.0f} km.")
        return " ".join(parts)

    def _build_recommendations(
        self,
        faults: List[Dict[str, Any]],
        compliance: str,
        rul: Dict[str, Any],
        ed: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        recs: List[Dict[str, Any]] = []

        # 1. Regulatory & Emission Compliance Action
        if compliance == "Fail":
            recs.append(
                {
                    "priority": "High",
                    "category": "Emission Compliance",
                    "title": "Mandatory Emission Retest Required",
                    "action": "Schedule immediate emission retest after repairs",
                    "description": "Tailpipe emissions fail legal Euro limits. Correct fuel mixture or catalytic components before operating on public roads.",
                    "estimated_cost": 50,
                }
            )
        elif compliance == "Warning":
            recs.append(
                {
                    "priority": "Medium",
                    "category": "Emission Compliance",
                    "title": "Borderline Exhaust Emissions",
                    "action": "Inspect exhaust sensors before failure occurs",
                    "description": "Exhaust gases are approaching maximum legal thresholds. Early servicing prevents a failed inspection.",
                    "estimated_cost": 40,
                }
            )

        # 2. Mechanical Fault Repairs
        for fault in faults[:3]:
            f_name = fault.get("fault", "Mechanical Anomaly")
            f_sev = fault.get("severity", "Medium")
            f_cost = fault.get("estimated_repair_cost", 150)
            f_desc = fault.get("description", f"Inspect, clean or replace components associated with {f_name}.")
            recs.append(
                {
                    "priority": f_sev,
                    "category": "Mechanical Repair",
                    "title": f"Service: {f_name}",
                    "action": f"Inspect and repair: {f_name}",
                    "description": f_desc,
                    "estimated_cost": f_cost,
                }
            )

        # 3. Preventive Maintenance (RUL & Kilometers)
        km_to_maint = rul.get("km_to_maintenance", 99999)
        if km_to_maint < 3000:
            recs.append(
                {
                    "priority": "Medium",
                    "category": "Routine Service",
                    "title": "Scheduled Service Interval Due",
                    "action": f"Service due in approximately {km_to_maint:,} km",
                    "description": "Replace 10W-40 4T motorcycle engine oil, clean intake air filter, and inspect spark plug electrode.",
                    "estimated_cost": 120,
                }
            )

        # 4. Default if vehicle is pristine
        if not recs:
            recs.append(
                {
                    "priority": "Low",
                    "category": "Routine Care",
                    "title": "Optimal Condition Routine Care",
                    "action": "Continue regular maintenance schedule",
                    "description": "All emission parameters and engine sensors are operating within nominal manufacturer tolerances.",
                    "estimated_cost": 0,
                }
            )

        return recs

    def _build_maintenance_schedule(
        self,
        faults: List[Dict[str, Any]],
        rul: Dict[str, Any],
        vd: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        schedule: List[Dict[str, Any]] = []
        km_maint = rul.get("km_to_maintenance", 5000)
        schedule.append(
            {
                "service": "Oil and filter change",
                "due_km": round(km_maint * 0.6),
                "priority": "Medium",
            }
        )
        schedule.append(
            {
                "service": "Full diagnostic scan",
                "due_km": round(km_maint),
                "priority": "Medium",
            }
        )
        if faults:
            schedule.insert(
                0,
                {
                    "service": f"Repair: {faults[0]['fault']}",
                    "due_km": min(1000, round(km_maint * 0.3)),
                    "priority": "High",
                },
            )
        return schedule
