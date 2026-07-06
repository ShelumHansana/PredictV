from typing import Optional
"""
Prediction ORM Model.

Stores ML prediction results including health scores, faults, RUL, and forecasts.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[Optional[str]] = mapped_column(String(36), primary_key=True)
    vehicle_id: Mapped[str] = mapped_column()
        String(36), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    emission_test_id: Mapped[str] = mapped_column()
        String(36), ForeignKey("emission_tests.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Health Score ─────────────────────────────
    health_score: Mapped[float] = mapped_column(Float, nullable=False)              # 0-100
    health_classification: Mapped[str] = mapped_column(String(20), nullable=False)  # Excellent/Good/...
    health_confidence: Mapped[float] = mapped_column(Float, nullable=False)         # 0-1

    # ── Emission Compliance ──────────────────────
    emission_compliance: Mapped[str] = mapped_column(String(20), nullable=False)    # Pass/Warning/Fail
    emission_details: Mapped[str] = mapped_column(Text, nullable=True)  # JSON details

    # ── Fault Detection ──────────────────────────
    detected_faults: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: [{fault, probability, severity}]
    fault_count: Mapped[Optional[int]] = mapped_column(default=0)
    primary_fault: Mapped[str] = mapped_column(String(100), nullable=True)
    primary_fault_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Remaining Useful Life ────────────────────
    remaining_life_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    km_to_maintenance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    km_to_major_repair: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    breakdown_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1

    # ── Predictive Analytics ─────────────────────
    forecast_30d: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON forecast
    forecast_90d: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    forecast_180d: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    forecast_365d: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Derived Insights ─────────────────────────
    estimated_repair_cost_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_repair_cost_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    urgency_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fuel_efficiency_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    environmental_impact_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    emission_rating: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # A-F grade

    # ── Explainability ───────────────────────────
    shap_values: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON SHAP values
    feature_importance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON feature importances
    explanation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Human-readable explanation

    # ── Recommendations ──────────────────────────
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    maintenance_schedule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON schedule

    # ── Model Metadata ───────────────────────────
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    overall_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column()
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    vehicle = relationship("Vehicle", back_populates="predictions")
    emission_test = relationship("EmissionTest", back_populates="predictions")

    def __repr__(self) -> str:
        return f"<Prediction(id={self.id}, health={self.health_score}, compliance={self.emission_compliance})>"
