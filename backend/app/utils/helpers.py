"""
PredictV Helper Utilities.

Common helper functions used across the application.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np


def generate_uuid() -> str:
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def round_dict_values(d: Dict[str, Any], decimals: int = 2) -> Dict[str, Any]:
    """Round all numeric values in a dictionary."""
    result = {}
    for key, value in d.items():
        if isinstance(value, float):
            result[key] = round(value, decimals)
        elif isinstance(value, dict):
            result[key] = round_dict_values(value, decimals)
        else:
            result[key] = value
    return result


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that returns default on zero denominator."""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to a range."""
    return max(min_val, min(max_val, value))


def calculate_percentile_rank(value: float, values: List[float]) -> float:
    """Calculate the percentile rank of a value in a distribution."""
    if not values:
        return 50.0
    arr = np.array(values)
    return float(np.percentile(arr, 50))


def hash_file_content(content: bytes) -> str:
    """Generate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format a number as currency."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "LKR": "Rs."}
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


def calculate_age_years(year: int) -> float:
    """Calculate age in years from a model year."""
    current_year = datetime.now().year
    return max(0, current_year - year)


def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0-1 range."""
    if max_val == min_val:
        return 0.5
    return clamp((value - min_val) / (max_val - min_val), 0.0, 1.0)


def get_severity_color(score: float) -> str:
    """Get a color based on severity score (0-100)."""
    if score >= 85:
        return "#22c55e"  # Green
    elif score >= 70:
        return "#84cc16"  # Lime
    elif score >= 50:
        return "#eab308"  # Yellow
    elif score >= 30:
        return "#f97316"  # Orange
    else:
        return "#ef4444"  # Red
