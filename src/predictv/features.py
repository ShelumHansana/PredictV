"""PredictV Feature Engineering Module (Petrol Motorbikes).

Transforms raw petrol motorbike emission + vehicle data into ML-ready
feature matrices.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Emission sensor columns ──────────────────────────────────
EMISSION_COLS = [
    "CO_percent", "CO2_percent", "HC_ppm", "O2_percent",
    "NOx_ppm", "Lambda", "Smoke_Opacity_percent",
]

ENGINE_COLS = [
    "engine_temperature_C", "rpm", "Fuel_Consumption_L100km",
]

VEHICLE_COLS = [
    "fuel_type", "vehicle_age_years", "mileage_km", "engine_cc",
]

CONDITION_COLS = [
    "Oil_Condition", "Catalytic_Converter",
]


class FeatureEngineer:
    """
    Builds derived features from raw petrol motorbike emission and vehicle data.

    Creates interaction terms, ratios, polynomial features, and
    categorical encodings to improve model accuracy.
    Designed exclusively for petrol-powered motorbikes.
    """

    # Mappings for categorical encoding
    FUEL_TYPE_MAP = {"Petrol": 0}  # Petrol motorbikes only
    OIL_CONDITION_MAP = {"Good": 0, "Average": 1, "Poor": 2, "Critical": 3}
    CATALYTIC_MAP = {"Working": 0, "Degraded": 1, "Failed": 2}

    def __init__(self) -> None:
        self.feature_names_: Optional[List[str]] = None

    def fit(self, df: pd.DataFrame) -> "FeatureEngineer":
        """Fit the feature engineer (learn feature names)."""
        transformed = self._transform(df)
        self.feature_names_ = list(transformed.columns)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw data into feature matrix."""
        return self._transform(df)

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit and transform in one step."""
        self.fit(df)
        return self.transform(df)

    def _transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal transform logic."""
        out = df.copy()

        # ── Categorical encoding ─────────────────────
        if "fuel_type" in out.columns:
            out["fuel_type_encoded"] = out["fuel_type"].map(self.FUEL_TYPE_MAP).fillna(0).astype(int)
        if "Oil_Condition" in out.columns:
            out["oil_condition_encoded"] = out["Oil_Condition"].map(self.OIL_CONDITION_MAP).fillna(0).astype(int)
        if "Catalytic_Converter" in out.columns:
            out["catalytic_encoded"] = out["Catalytic_Converter"].map(self.CATALYTIC_MAP).fillna(0).astype(int)

        # ── Derived ratios ───────────────────────────
        if "CO_percent" in out.columns and "CO2_percent" in out.columns:
            out["co_co2_ratio"] = out["CO_percent"] / out["CO2_percent"].replace(0, np.nan)
            out["co_co2_ratio"] = out["co_co2_ratio"].fillna(0)

        if "HC_ppm" in out.columns and "NOx_ppm" in out.columns:
            out["hc_nox_ratio"] = out["HC_ppm"] / out["NOx_ppm"].replace(0, np.nan)
            out["hc_nox_ratio"] = out["hc_nox_ratio"].fillna(0)

        if "O2_percent" in out.columns and "CO2_percent" in out.columns:
            out["combustion_efficiency"] = out["CO2_percent"] / (out["CO2_percent"] + out["O2_percent"]).replace(0, np.nan)
            out["combustion_efficiency"] = out["combustion_efficiency"].fillna(0)

        # ── Lambda deviation ─────────────────────────
        if "Lambda" in out.columns:
            out["lambda_deviation"] = (out["Lambda"] - 1.0).abs()

        # ── Mileage-age interaction ──────────────────
        if "mileage_km" in out.columns and "vehicle_age_years" in out.columns:
            age_safe = out["vehicle_age_years"].replace(0, 1)
            out["km_per_year"] = out["mileage_km"] / age_safe
            out["mileage_age_interaction"] = out["mileage_km"] * out["vehicle_age_years"]

        # ── Engine stress indicator ──────────────────
        if "engine_temperature_C" in out.columns and "rpm" in out.columns:
            out["engine_stress"] = out["engine_temperature_C"] * out["rpm"] / 1e5

        # ── Emission severity index ──────────────────
        emission_cols_present = [c for c in EMISSION_COLS if c in out.columns]
        if emission_cols_present:
            # Z-score-like severity
            for col in emission_cols_present:
                mean_val = out[col].mean()
                std_val = out[col].std()
                if std_val > 0:
                    out[f"{col}_zscore"] = (out[col] - mean_val) / std_val

        # ── Fuel efficiency per cc ───────────────────
        if "Fuel_Consumption_L100km" in out.columns and "engine_cc" in out.columns:
            out["fuel_per_cc"] = out["Fuel_Consumption_L100km"] / out["engine_cc"].replace(0, np.nan)
            out["fuel_per_cc"] = out["fuel_per_cc"].fillna(0)

        # ── Drop original categoricals ───────────────
        cols_to_drop = ["vehicle_id", "fuel_type", "Oil_Condition", "Catalytic_Converter",
                        "Emission_Test", "Engine_Status", "Maintenance_Required"]
        out = out.drop(columns=[c for c in cols_to_drop if c in out.columns], errors="ignore")

        # Fill remaining NaN
        out = out.fillna(0)

        return out

    def get_feature_names(self) -> List[str]:
        """Return the list of feature names after transformation."""
        if self.feature_names_ is None:
            raise RuntimeError("FeatureEngineer has not been fit yet.")
        return self.feature_names_
