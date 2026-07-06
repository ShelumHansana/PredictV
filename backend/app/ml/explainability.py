"""
Explainable AI Module for PredictV.

Implements SHAP and LIME for explaining ML predictions.
Provides feature importance, waterfall data, and human-readable explanations.
"""

import warnings
from typing import Any, Dict, List, Optional

import numpy as np

warnings.filterwarnings("ignore")

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

try:
    import lime
    import lime.lime_tabular
    HAS_LIME = True
except ImportError:
    HAS_LIME = False


class ExplainabilityEngine:
    """Provides SHAP and LIME explanations for predictions."""

    def __init__(self):
        self.shap_explainer: Optional[Any] = None
        self.lime_explainer: Optional[Any] = None
        self.feature_names: List[str] = []
        self.training_data: Optional[np.ndarray] = None

    def setup(
        self,
        model: Any,
        X_train: np.ndarray,
        feature_names: List[str],
        model_type: str = "tree",
    ) -> None:
        """Initialize SHAP and LIME explainers with training data."""
        self.feature_names = feature_names
        self.training_data = X_train

        # Setup SHAP
        if HAS_SHAP:
            try:
                if model_type == "tree":
                    # Use a small background sample for efficiency
                    sample_size = min(100, X_train.shape[0])
                    bg = X_train[np.random.choice(X_train.shape[0], sample_size, replace=False)]
                    self.shap_explainer = shap.TreeExplainer(model, data=bg)
                else:
                    bg = shap.sample(X_train, min(50, X_train.shape[0]))
                    self.shap_explainer = shap.KernelExplainer(model.predict, bg)
            except Exception:
                self.shap_explainer = None

        # Setup LIME
        if HAS_LIME:
            try:
                self.lime_explainer = lime.lime_tabular.LimeTabularExplainer(
                    training_data=X_train,
                    feature_names=feature_names,
                    mode="regression",
                    discretize_continuous=True,
                )
            except Exception:
                self.lime_explainer = None

    def explain_shap(self, X: np.ndarray) -> Dict[str, Any]:
        """Generate SHAP explanation for a prediction."""
        if not HAS_SHAP or self.shap_explainer is None:
            return self._fallback_explanation(X)

        X_input = X.reshape(1, -1) if X.ndim == 1 else X

        try:
            shap_values = self.shap_explainer.shap_values(X_input)

            # Handle multi-output
            if isinstance(shap_values, list):
                sv = shap_values[0] if len(shap_values) > 0 else shap_values
            else:
                sv = shap_values

            if sv.ndim > 1:
                sv = sv[0]

            # Build feature contribution dict
            contributions = {}
            for i, fname in enumerate(self.feature_names):
                if i < len(sv):
                    contributions[fname] = round(float(sv[i]), 4)

            # Sort by absolute value
            sorted_contributions = dict(
                sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
            )

            # Top positive and negative contributors
            positive = {k: v for k, v in sorted_contributions.items() if v > 0}
            negative = {k: v for k, v in sorted_contributions.items() if v < 0}

            return {
                "method": "SHAP",
                "contributions": sorted_contributions,
                "top_positive": dict(list(positive.items())[:5]),
                "top_negative": dict(list(negative.items())[:5]),
                "base_value": float(self.shap_explainer.expected_value)
                    if hasattr(self.shap_explainer, "expected_value")
                    and not isinstance(self.shap_explainer.expected_value, (list, np.ndarray))
                    else None,
            }
        except Exception as e:
            return {"method": "SHAP", "error": str(e), **self._fallback_explanation(X)}

    def explain_lime(self, X: np.ndarray, model: Any) -> Dict[str, Any]:
        """Generate LIME explanation for a prediction."""
        if not HAS_LIME or self.lime_explainer is None:
            return self._fallback_explanation(X)

        X_input = X.flatten() if X.ndim > 1 else X

        try:
            explanation = self.lime_explainer.explain_instance(
                X_input,
                model.predict,
                num_features=min(15, len(self.feature_names)),
            )

            feature_weights = {}
            for feature, weight in explanation.as_list():
                feature_weights[feature] = round(weight, 4)

            return {
                "method": "LIME",
                "feature_weights": feature_weights,
                "intercept": round(float(explanation.intercept[0])
                    if hasattr(explanation, "intercept") else 0, 4),
                "prediction_local": round(float(explanation.local_pred[0])
                    if hasattr(explanation, "local_pred") else 0, 4),
            }
        except Exception as e:
            return {"method": "LIME", "error": str(e)}

    def _fallback_explanation(self, X: np.ndarray) -> Dict[str, Any]:
        """Provide a rule-based explanation when SHAP/LIME unavailable."""
        explanations = {}
        if X.ndim > 1:
            X = X.flatten()

        for i, fname in enumerate(self.feature_names):
            if i < len(X):
                explanations[fname] = round(float(X[i]), 4)

        return {
            "method": "feature_values",
            "feature_values": dict(
                sorted(explanations.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
            ),
        }

    def generate_explanation_text(
        self,
        shap_result: Dict[str, Any],
        health_score: float,
        faults: List[str],
    ) -> str:
        """Generate human-readable explanation text."""
        lines = []
        lines.append(f"Engine Health Score: {health_score:.1f}/100")
        lines.append("")

        # Key contributing factors
        if "contributions" in shap_result:
            top_factors = list(shap_result["contributions"].items())[:5]
            lines.append("Key factors influencing this score:")
            for feature, contribution in top_factors:
                direction = "↑ improving" if contribution > 0 else "↓ reducing"
                clean_name = feature.replace("_", " ").title()
                lines.append(f"  • {clean_name}: {direction} health by {abs(contribution):.2f}")

        # Faults
        if faults:
            lines.append("")
            lines.append(f"Detected Issues ({len(faults)}):")
            for fault in faults[:5]:
                lines.append(f"  ⚠ {fault}")

        return "\n".join(lines)

    def get_feature_importance(self, model: Any) -> Dict[str, float]:
        """Extract feature importance from a model."""
        try:
            importances = model.feature_importances_
            importance_dict = dict(zip(self.feature_names, importances))
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        except AttributeError:
            return {}
