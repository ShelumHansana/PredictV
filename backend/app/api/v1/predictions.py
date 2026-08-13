"""
Prediction API Routes.

Retrieve prediction results and history.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.models.vehicle import Vehicle

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/{prediction_id}")
async def get_prediction(
    prediction_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single prediction result by ID."""
    result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    # Access check
    if user.role != "admin":
        vehicle = await db.execute(select(Vehicle).where(Vehicle.id == prediction.vehicle_id))
        v = vehicle.scalar_one_or_none()
        if not v or v.owner_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    return _format_prediction(prediction)


@router.get("/vehicle/{vehicle_id}")
async def get_vehicle_predictions(
    vehicle_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get prediction history for a vehicle."""
    result = await db.execute(
        select(Prediction)
        .where(Prediction.vehicle_id == vehicle_id)
        .order_by(Prediction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    predictions = result.scalars().all()
    return [_format_prediction(p) for p in predictions]


@router.get("/history/all")
async def get_all_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all predictions for the current user."""
    query = select(Prediction)

    if user.role != "admin":
        # Get user's vehicle IDs
        vehicles_result = await db.execute(
            select(Vehicle.id).where(Vehicle.owner_id == user.id)
        )
        vehicle_ids = [v[0] for v in vehicles_result.all()]
        if not vehicle_ids:
            return []
        query = query.where(Prediction.vehicle_id.in_(vehicle_ids))

    result = await db.execute(
        query.order_by(Prediction.created_at.desc()).offset(skip).limit(limit)
    )
    predictions = result.scalars().all()
    return [_format_prediction(p) for p in predictions]


def _format_prediction(p: Prediction) -> dict:
    """Format a prediction ORM object for API response."""
    def safe_json(val):
        if val is None:
            return None
        if isinstance(val, str):
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return val
        return val

    return {
        "id": p.id,
        "vehicle_id": p.vehicle_id,
        "emission_test_id": p.emission_test_id,
        "health_score": p.health_score,
        "health_classification": p.health_classification,
        "health_confidence": p.health_confidence,
        "emission_compliance": p.emission_compliance,
        "emission_details": safe_json(p.emission_details),
        "detected_faults": safe_json(p.detected_faults),
        "fault_count": p.fault_count,
        "primary_fault": p.primary_fault,
        "primary_fault_probability": p.primary_fault_probability,
        "remaining_life_km": p.remaining_life_km,
        "km_to_maintenance": p.km_to_maintenance,
        "km_to_major_repair": p.km_to_major_repair,
        "breakdown_probability": p.breakdown_probability,
        "forecast_30d": safe_json(p.forecast_30d),
        "forecast_90d": safe_json(p.forecast_90d),
        "forecast_180d": safe_json(p.forecast_180d),
        "forecast_365d": safe_json(p.forecast_365d),
        "estimated_repair_cost_min": p.estimated_repair_cost_min,
        "estimated_repair_cost_max": p.estimated_repair_cost_max,
        "risk_level": p.risk_level,
        "urgency_level": p.urgency_level,
        "fuel_efficiency_rating": p.fuel_efficiency_rating,
        "environmental_impact_score": p.environmental_impact_score,
        "emission_rating": p.emission_rating,
        "feature_importance": safe_json(p.feature_importance),
        "explanation_text": p.explanation_text,
        "recommendations": safe_json(p.recommendations),
        "maintenance_schedule": safe_json(p.maintenance_schedule),
        "model_version": p.model_version,
        "overall_confidence": p.overall_confidence,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
