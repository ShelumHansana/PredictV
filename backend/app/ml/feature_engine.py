"""
Feature Engineering for PredictV ML Pipeline.

Creates derived, interaction, and domain-specific features
based on automotive engineering principles.
"""

from typing import List

import numpy as np
import pandas as pd


class FeatureEngineer:
    """Generates engineered features from raw emission and sensor data."""

    def __init__(self):
        self.derived_feature_names: List[str] = []

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all feature engineering transformations."""
        df = df.copy()
        df = self._add_emission_ratios(df)
        df = self._add_combustion_features(df)
        df = self._add_sensor_interactions(df)
        df = self._add_vehicle_features(df)
        df = self._add_anomaly_scores(df)
        return df

    def _add_emission_ratios(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add emission ratio features that indicate combustion quality."""
        # CO/CO₂ ratio — high indicates incomplete combustion
        if "co_percent" in df.columns and "co2_percent" in df.columns:
            df["co_co2_ratio"] = df["co_percent"] / df["co2_percent"].clip(lower=0.1)
            self.derived_feature_names.append("co_co2_ratio")

        # HC/NOx ratio — indicates lean vs rich tendency
        if "hc_ppm" in df.columns and "nox_ppm" in df.columns:
            df["hc_nox_ratio"] = df["hc_ppm"] / df["nox_ppm"].clip(lower=1)
            self.derived_feature_names.append("hc_nox_ratio")

        # Lambda deviation from stoichiometric
        if "lambda_value" in df.columns:
            df["lambda_deviation"] = abs(df["lambda_value"] - 1.0)
            self.derived_feature_names.append("lambda_deviation")

        # Emission severity index (normalized composite)
        if all(c in df.columns for c in ["co_percent", "hc_ppm", "nox_ppm"]):
            df["emission_severity_index"] = (
                df["co_percent"] / 0.5 +
                df["hc_ppm"] / 200 +
                df["nox_ppm"] / 100
            ) / 3
            self.derived_feature_names.append("emission_severity_index")

        return df

    def _add_combustion_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features that indicate combustion efficiency."""
        # Combustion efficiency estimate
        if "co2_percent" in df.columns and "co_percent" in df.columns:
            total_carbon = df["co2_percent"] + df["co_percent"]
            df["combustion_efficiency"] = df["co2_percent"] / total_carbon.clip(lower=0.1) * 100
            self.derived_feature_names.append("combustion_efficiency")

        # Air-fuel ratio deviation from stoichiometric (14.7 for petrol)
        if "air_fuel_ratio" in df.columns:
            df["afr_deviation"] = abs(df["air_fuel_ratio"] - 14.7)
            df["afr_rich_lean"] = np.where(df["air_fuel_ratio"] < 14.7, -1, 1)
            self.derived_feature_names.extend(["afr_deviation", "afr_rich_lean"])

        # Exhaust temperature anomaly (deviation from normal range)
        if "exhaust_temp" in df.columns:
            df["exhaust_temp_anomaly"] = abs(df["exhaust_temp"] - 350) / 100
            self.derived_feature_names.append("exhaust_temp_anomaly")

        return df

    def _add_sensor_interactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add interaction features between sensors."""
        # RPM × Load = approximate power output
        if "engine_rpm" in df.columns and "engine_load" in df.columns:
            df["rpm_load_product"] = df["engine_rpm"] * df["engine_load"] / 1000
            self.derived_feature_names.append("rpm_load_product")

        # Temperature delta (oil vs coolant — high delta indicates issues)
        if "oil_temp" in df.columns and "coolant_temp" in df.columns:
            df["temp_delta_oil_coolant"] = df["oil_temp"] - df["coolant_temp"]
            self.derived_feature_names.append("temp_delta_oil_coolant")

        # Temperature delta (exhaust vs coolant)
        if "exhaust_temp" in df.columns and "coolant_temp" in df.columns:
            df["temp_delta_exhaust_coolant"] = df["exhaust_temp"] - df["coolant_temp"]
            self.derived_feature_names.append("temp_delta_exhaust_coolant")

        # MAP/MAF ratio — indicates volumetric efficiency
        if "map_sensor" in df.columns and "maf_sensor" in df.columns:
            df["map_maf_ratio"] = df["map_sensor"] / df["maf_sensor"].clip(lower=0.1)
            self.derived_feature_names.append("map_maf_ratio")

        # Fuel efficiency indicator
        if "fuel_consumption" in df.columns and "engine_load" in df.columns:
            df["fuel_efficiency_indicator"] = df["engine_load"] / df["fuel_consumption"].clip(lower=0.1)
            self.derived_feature_names.append("fuel_efficiency_indicator")

        # O₂ sensor vs lambda consistency
        if "o2_sensor_reading" in df.columns and "lambda_value" in df.columns:
            df["o2_lambda_consistency"] = abs(
                df["o2_sensor_reading"] - (1 - (df["lambda_value"] - 1).clip(-0.5, 0.5))
            )
            self.derived_feature_names.append("o2_lambda_consistency")

        return df

    def _add_vehicle_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add vehicle-derived features."""
        # Vehicle age (if year column exists)
        if "year" in df.columns:
            current_year = 2026
            df["vehicle_age"] = current_year - df["year"]
            if "vehicle_age" not in self.derived_feature_names:
                self.derived_feature_names.append("vehicle_age")

        # Mileage per year (usage intensity)
        if "mileage" in df.columns and "vehicle_age" in df.columns:
            df["mileage_per_year"] = df["mileage"] / df["vehicle_age"].clip(lower=1)
            self.derived_feature_names.append("mileage_per_year")

        # High mileage flag
        if "mileage" in df.columns:
            df["high_mileage"] = (df["mileage"] > 150000).astype(int)
            self.derived_feature_names.append("high_mileage")

        return df

    def _add_anomaly_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add anomaly score features based on deviation from normal ranges."""
        anomaly_configs = {
            "coolant_temp": {"normal": 90, "scale": 10},
            "oil_temp": {"normal": 95, "scale": 10},
            "battery_voltage": {"normal": 13.8, "scale": 0.5},
            "fuel_pressure": {"normal": 350, "scale": 30},
            "catalytic_efficiency": {"normal": 96, "scale": 5},
        }

        for col, config in anomaly_configs.items():
            if col in df.columns:
                score_name = f"{col}_anomaly_score"
                df[score_name] = abs(df[col] - config["normal"]) / config["scale"]
                self.derived_feature_names.append(score_name)

        # Total anomaly score
        anomaly_cols = [c for c in df.columns if c.endswith("_anomaly_score")]
        if anomaly_cols:
            df["total_anomaly_score"] = df[anomaly_cols].sum(axis=1)
            self.derived_feature_names.append("total_anomaly_score")

        return df

    def get_feature_names(self) -> List[str]:
        """Return all derived feature names."""
        return list(set(self.derived_feature_names))
