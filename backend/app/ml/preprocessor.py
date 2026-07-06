"""
Data Preprocessor for PredictV ML Pipeline.

Handles missing values, normalization, outlier detection, and encoding.
"""

import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

from app.utils.constants import ALL_FEATURES, EMISSION_FEATURES, SENSOR_FEATURES

warnings.filterwarnings("ignore")


class DataPreprocessor:
    """Preprocesses emission and sensor data for ML model consumption."""

    def __init__(self):
        self.scaler: Optional[StandardScaler] = None
        self.minmax_scaler: Optional[MinMaxScaler] = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.imputer: Optional[KNNImputer] = None
        self.feature_names: List[str] = []
        self.is_fitted: bool = False
        self._medians: Dict[str, float] = {}

    def fit(self, df: pd.DataFrame) -> "DataPreprocessor":
        """Fit the preprocessor on training data."""
        df = df.copy()

        # Store medians for imputation
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        self._medians = df[numeric_cols].median().to_dict()

        # Fit label encoders for categorical columns
        categorical_cols = ["fuel_type", "brand", "climate", "driving_condition"]
        for col in categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                # Handle unseen values by adding an 'unknown' category
                values = df[col].fillna("unknown").astype(str).values
                le.fit(np.append(values, "unknown"))
                self.label_encoders[col] = le

        # Fit imputer
        feature_cols = [c for c in ALL_FEATURES if c in df.columns]
        if feature_cols:
            self.imputer = KNNImputer(n_neighbors=5)
            self.imputer.fit(df[feature_cols].values)

        # Fit scaler
        self.scaler = StandardScaler()
        self.minmax_scaler = MinMaxScaler()
        if feature_cols:
            self.scaler.fit(df[feature_cols].values)
            self.minmax_scaler.fit(df[feature_cols].values)

        self.feature_names = feature_cols
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame, normalize: bool = True) -> pd.DataFrame:
        """Transform data using fitted preprocessor."""
        df = df.copy()

        # Handle missing values
        df = self._impute_missing(df)

        # Encode categoricals
        df = self._encode_categoricals(df)

        # Detect and clip outliers
        df = self._handle_outliers(df)

        # Normalize numeric features
        if normalize and self.scaler is not None:
            feature_cols = [c for c in self.feature_names if c in df.columns]
            if feature_cols:
                df[feature_cols] = self.scaler.transform(df[feature_cols].values)

        return df

    def fit_transform(self, df: pd.DataFrame, normalize: bool = True) -> pd.DataFrame:
        """Fit and transform in one step."""
        self.fit(df)
        return self.transform(df, normalize=normalize)

    def _impute_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values using KNN imputation for sensor data, median for others."""
        # First, fill with medians as a fallback
        for col, median_val in self._medians.items():
            if col in df.columns and df[col].isnull().any():
                df[col] = df[col].fillna(median_val)

        # KNN imputation for sensor features if fitted
        if self.imputer is not None:
            feature_cols = [c for c in self.feature_names if c in df.columns]
            if feature_cols:
                mask = df[feature_cols].isnull().any(axis=1)
                if mask.any():
                    df.loc[:, feature_cols] = self.imputer.transform(df[feature_cols].values)

        return df

    def _encode_categoricals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical variables."""
        for col, le in self.label_encoders.items():
            if col in df.columns:
                # Handle unseen categories
                known_classes = set(le.classes_)
                df[f"{col}_encoded"] = df[col].apply(
                    lambda x: le.transform([str(x)])[0] if str(x) in known_classes
                    else le.transform(["unknown"])[0]
                )
        return df

    def _handle_outliers(self, df: pd.DataFrame, iqr_factor: float = 3.0) -> pd.DataFrame:
        """Detect and clip outliers using IQR method."""
        numeric_cols = [c for c in self.feature_names if c in df.columns]
        for col in numeric_cols:
            if df[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                q1 = df[col].quantile(0.01)
                q3 = df[col].quantile(0.99)
                iqr = q3 - q1
                lower = q1 - iqr_factor * iqr
                upper = q3 + iqr_factor * iqr
                df[col] = df[col].clip(lower, upper)
        return df

    def prepare_features(
        self, df: pd.DataFrame, target_col: Optional[str] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray], List[str]]:
        """Extract feature matrix and optionally the target vector."""
        feature_cols = [c for c in self.feature_names if c in df.columns]

        # Add encoded categorical features
        encoded_cols = [c for c in df.columns if c.endswith("_encoded")]
        all_feature_cols = feature_cols + encoded_cols

        X = df[all_feature_cols].values.astype(np.float32)
        feature_names = all_feature_cols

        y = None
        if target_col and target_col in df.columns:
            y = df[target_col].values

        return X, y, feature_names

    def prepare_single_record(self, data: Dict) -> np.ndarray:
        """Prepare a single record (from API input) for prediction."""
        df = pd.DataFrame([data])
        df = self.transform(df, normalize=True)
        X, _, _ = self.prepare_features(df)
        return X
