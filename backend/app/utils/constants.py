"""
PredictV Constants.

Emission legal limits, thresholds, fault definitions, and system constants.
Based on Euro 6 / EPA Tier 3 emission standards.
"""

from enum import Enum
from typing import Dict, List


# ──────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────

class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    LPG = "lpg"
    CNG = "cng"


class UserRole(str, Enum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    OWNER = "owner"


class HealthClassification(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    MODERATE = "Moderate"
    POOR = "Poor"
    CRITICAL = "Critical"


class EmissionCompliance(str, Enum):
    PASS = "Pass"
    WARNING = "Warning"
    FAIL = "Fail"


class UrgencyLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# ──────────────────────────────────────────────
# Emission Legal Limits (Euro 6 standards)
# ──────────────────────────────────────────────

EMISSION_LIMITS_PETROL = {
    "co_percent": {"pass": 0.3, "warning": 0.5, "unit": "%"},
    "co2_percent": {"pass": 14.5, "warning": 13.0, "unit": "%"},  # lower is worse
    "hc_ppm": {"pass": 100, "warning": 150, "unit": "ppm"},
    "o2_percent": {"pass": 1.0, "warning": 2.0, "unit": "%"},  # lower is better at idle
    "nox_ppm": {"pass": 60, "warning": 100, "unit": "ppm"},
    "lambda_value": {"pass_low": 0.97, "pass_high": 1.03, "warning_low": 0.95, "warning_high": 1.05},
    "smoke_opacity": {"pass": 10, "warning": 20, "unit": "%"},
}

EMISSION_LIMITS_DIESEL = {
    "co_percent": {"pass": 0.5, "warning": 0.8, "unit": "%"},
    "co2_percent": {"pass": 13.0, "warning": 11.0, "unit": "%"},
    "hc_ppm": {"pass": 200, "warning": 300, "unit": "ppm"},
    "o2_percent": {"pass": 3.0, "warning": 5.0, "unit": "%"},
    "nox_ppm": {"pass": 80, "warning": 150, "unit": "ppm"},
    "lambda_value": {"pass_low": 1.0, "pass_high": 1.8, "warning_low": 0.95, "warning_high": 2.0},
    "smoke_opacity": {"pass": 30, "warning": 50, "unit": "%"},
}

EMISSION_LIMITS = {
    FuelType.PETROL: EMISSION_LIMITS_PETROL,
    FuelType.DIESEL: EMISSION_LIMITS_DIESEL,
    FuelType.HYBRID: EMISSION_LIMITS_PETROL,
    FuelType.LPG: EMISSION_LIMITS_PETROL,
    FuelType.CNG: EMISSION_LIMITS_PETROL,
}


# ──────────────────────────────────────────────
# Normal Operating Ranges
# ──────────────────────────────────────────────

NORMAL_RANGES = {
    "exhaust_temp": {"min": 150, "max": 600, "unit": "°C"},
    "engine_rpm": {"idle_min": 650, "idle_max": 900, "max": 7000, "unit": "RPM"},
    "air_fuel_ratio": {"stoich": 14.7, "min": 12.0, "max": 17.0},
    "oil_temp": {"min": 80, "max": 120, "unit": "°C"},
    "coolant_temp": {"min": 80, "max": 105, "unit": "°C"},
    "engine_load": {"idle": 20, "max": 100, "unit": "%"},
    "throttle_position": {"idle": 5, "max": 100, "unit": "%"},
    "fuel_pressure": {"min": 250, "max": 400, "unit": "kPa"},
    "turbo_pressure": {"min": 0.5, "max": 2.5, "unit": "bar"},
    "o2_sensor": {"min": 0.1, "max": 0.9, "unit": "V"},
    "catalytic_efficiency": {"good": 95, "warning": 85, "unit": "%"},
    "maf_sensor": {"min": 2, "max": 300, "unit": "g/s"},
    "map_sensor": {"idle": 30, "max": 105, "unit": "kPa"},
    "battery_voltage": {"min": 12.0, "max": 14.8, "unit": "V"},
}


# ──────────────────────────────────────────────
# Fault Definitions
# ──────────────────────────────────────────────

FAULT_TYPES: List[str] = [
    "Dirty Air Filter",
    "Bad Spark Plug",
    "Injector Problem",
    "Fuel Pump Issue",
    "Turbo Failure",
    "Catalytic Converter Failure",
    "Faulty Oxygen Sensor",
    "Vacuum Leak",
    "Poor Compression",
    "Engine Misfire",
    "Oil Burning",
    "Coolant Leakage",
    "Rich Fuel Mixture",
    "Lean Fuel Mixture",
    "EGR Failure",
    "DPF Blockage",
    "Valve Wear",
    "Piston Ring Wear",
    "Head Gasket Issue",
    "Timing Problem",
    "Sensor Failure",
]

# Fault symptom signatures — which emission/sensor patterns indicate which fault
FAULT_SIGNATURES: Dict[str, Dict[str, str]] = {
    "Dirty Air Filter": {
        "co_trend": "high", "hc_trend": "high", "o2_trend": "low",
        "maf_trend": "low", "fuel_efficiency_trend": "low",
        "severity": "low", "avg_repair_cost": "50",
    },
    "Bad Spark Plug": {
        "hc_trend": "high", "co_trend": "high", "misfire": "true",
        "engine_roughness": "high", "fuel_efficiency_trend": "low",
        "severity": "medium", "avg_repair_cost": "150",
    },
    "Injector Problem": {
        "hc_trend": "high", "co_trend": "high", "fuel_pressure_trend": "unstable",
        "lambda_deviation": "high", "engine_roughness": "high",
        "severity": "high", "avg_repair_cost": "400",
    },
    "Fuel Pump Issue": {
        "fuel_pressure_trend": "low", "engine_stall": "possible",
        "power_loss": "true", "hard_start": "true",
        "severity": "high", "avg_repair_cost": "600",
    },
    "Turbo Failure": {
        "turbo_pressure_trend": "low", "power_loss": "true",
        "smoke_trend": "high", "oil_consumption": "high",
        "severity": "critical", "avg_repair_cost": "2000",
    },
    "Catalytic Converter Failure": {
        "catalytic_efficiency_trend": "low", "nox_trend": "high",
        "hc_trend": "high", "co_trend": "high",
        "severity": "critical", "avg_repair_cost": "1500",
    },
    "Faulty Oxygen Sensor": {
        "lambda_deviation": "high", "o2_sensor_trend": "stuck",
        "fuel_efficiency_trend": "low", "co_trend": "unstable",
        "severity": "medium", "avg_repair_cost": "250",
    },
    "Vacuum Leak": {
        "map_trend": "high", "idle_trend": "rough", "hc_trend": "high",
        "lean_mixture": "true", "hissing_noise": "true",
        "severity": "medium", "avg_repair_cost": "200",
    },
    "Poor Compression": {
        "power_loss": "true", "hc_trend": "high", "co_trend": "high",
        "oil_consumption": "high", "hard_start": "true",
        "severity": "critical", "avg_repair_cost": "2500",
    },
    "Engine Misfire": {
        "hc_trend": "very_high", "rpm_instability": "high",
        "vibration": "high", "power_loss": "true",
        "severity": "high", "avg_repair_cost": "300",
    },
    "Oil Burning": {
        "smoke_trend": "blue", "oil_consumption": "high",
        "hc_trend": "high", "spark_plug_fouling": "true",
        "severity": "high", "avg_repair_cost": "1800",
    },
    "Coolant Leakage": {
        "coolant_temp_trend": "high", "coolant_level": "low",
        "white_smoke": "true", "overheating": "possible",
        "severity": "critical", "avg_repair_cost": "800",
    },
    "Rich Fuel Mixture": {
        "co_trend": "high", "lambda_trend": "low", "o2_trend": "low",
        "fuel_efficiency_trend": "low", "black_smoke": "possible",
        "severity": "medium", "avg_repair_cost": "200",
    },
    "Lean Fuel Mixture": {
        "nox_trend": "high", "lambda_trend": "high", "o2_trend": "high",
        "exhaust_temp_trend": "high", "engine_knock": "possible",
        "severity": "medium", "avg_repair_cost": "200",
    },
    "EGR Failure": {
        "nox_trend": "high", "engine_roughness": "high",
        "carbon_buildup": "true", "power_loss": "possible",
        "severity": "high", "avg_repair_cost": "500",
    },
    "DPF Blockage": {
        "smoke_opacity_trend": "high", "back_pressure": "high",
        "power_loss": "true", "regen_failure": "true",
        "severity": "high", "avg_repair_cost": "1200",
    },
    "Valve Wear": {
        "compression_loss": "true", "power_loss": "true",
        "hc_trend": "high", "ticking_noise": "true",
        "severity": "high", "avg_repair_cost": "1500",
    },
    "Piston Ring Wear": {
        "oil_consumption": "high", "compression_loss": "true",
        "blue_smoke": "true", "power_loss": "true",
        "severity": "critical", "avg_repair_cost": "3000",
    },
    "Head Gasket Issue": {
        "coolant_in_oil": "true", "white_smoke": "true",
        "overheating": "true", "compression_loss": "true",
        "severity": "critical", "avg_repair_cost": "2000",
    },
    "Timing Problem": {
        "engine_roughness": "high", "power_loss": "true",
        "backfire": "possible", "hard_start": "true",
        "severity": "critical", "avg_repair_cost": "800",
    },
    "Sensor Failure": {
        "erratic_readings": "true", "check_engine_light": "true",
        "poor_performance": "possible",
        "severity": "medium", "avg_repair_cost": "300",
    },
}

# Health score thresholds
HEALTH_CLASSIFICATION_THRESHOLDS = {
    HealthClassification.EXCELLENT: (85, 100),
    HealthClassification.GOOD: (70, 84),
    HealthClassification.MODERATE: (50, 69),
    HealthClassification.POOR: (30, 49),
    HealthClassification.CRITICAL: (0, 29),
}


def classify_health(score: float) -> HealthClassification:
    """Classify a health score into a category."""
    score = max(0, min(100, score))
    for classification, (low, high) in HEALTH_CLASSIFICATION_THRESHOLDS.items():
        if low <= score <= high:
            return classification
    return HealthClassification.CRITICAL


# Average repair costs by fault type
REPAIR_COSTS: Dict[str, Dict[str, float]] = {
    fault: {
        "min": float(sig["avg_repair_cost"]) * 0.6,
        "avg": float(sig["avg_repair_cost"]),
        "max": float(sig["avg_repair_cost"]) * 1.5,
    }
    for fault, sig in FAULT_SIGNATURES.items()
}

# Prediction horizons in days
PREDICTION_HORIZONS = [30, 90, 180, 365]

# Feature columns for ML models
EMISSION_FEATURES = [
    "co_percent", "co2_percent", "hc_ppm", "o2_percent", "nox_ppm",
    "lambda_value", "smoke_opacity",
]

SENSOR_FEATURES = [
    "exhaust_temp", "engine_rpm", "air_fuel_ratio", "oil_temp",
    "coolant_temp", "ambient_temp", "relative_humidity", "engine_load",
    "throttle_position", "fuel_consumption", "fuel_pressure",
    "turbo_pressure", "o2_sensor_reading", "catalytic_efficiency",
    "maf_sensor", "map_sensor", "battery_voltage", "engine_running_time",
]

VEHICLE_FEATURES = [
    "engine_capacity", "mileage", "vehicle_age",
]

ALL_FEATURES = EMISSION_FEATURES + SENSOR_FEATURES + VEHICLE_FEATURES
