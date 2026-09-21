"""
Emission & Analysis API Routes (Petrol Motorbikes).

Upload emission data, run ML analysis, and manage emission test records.
Only petrol motorbike vehicles are supported for analysis.
"""

import io
import json
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.ml.pipeline import PredictionPipeline
from app.models.emission_test import EmissionTest
from app.models.prediction import Prediction
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    EmissionTestCreate,
    EmissionTestResponse,
    FileUploadResponse,
    ManualBikePredictionRequest,
    ManualBikePredictionResponse,
)
from app.utils.helpers import generate_uuid, utc_now

router = APIRouter(prefix="/emissions", tags=["Emissions & Analysis"])

# Global prediction pipeline (loaded on startup)
_pipeline: Optional[PredictionPipeline] = None


def get_pipeline() -> PredictionPipeline:
    """Get or initialize the prediction pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = PredictionPipeline()
        _pipeline.load_models()
    return _pipeline


@router.post("/", response_model=EmissionTestResponse, status_code=status.HTTP_201_CREATED)
async def create_emission_test(
    data: EmissionTestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new emission test record."""
    # Verify vehicle access
    result = await db.execute(select(Vehicle).where(Vehicle.id == data.vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if user.role != "admin" and vehicle.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    test = EmissionTest(
        id=generate_uuid(),
        **data.model_dump(),
    )
    db.add(test)
    await db.flush()
    await db.refresh(test)
    return test


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_emission(
    data: AnalysisRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run a full ML analysis on an emission test."""
    # Get emission test
    result = await db.execute(
        select(EmissionTest).where(EmissionTest.id == data.emission_test_id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Emission test not found")

    # Get vehicle
    result = await db.execute(select(Vehicle).where(Vehicle.id == test.vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Validate fuel type — petrol motorbikes only
    if vehicle.fuel_type and vehicle.fuel_type.lower() != "petrol":
        raise HTTPException(
            status_code=400,
            detail=f"PredictV only supports petrol motorbikes. This vehicle uses '{vehicle.fuel_type}'.",
        )

    # Prepare data for ML pipeline
    emission_data = {
        "co_percent": test.co_percent or 0.1,
        "co2_percent": test.co2_percent or 14.0,
        "hc_ppm": test.hc_ppm or 50,
        "o2_percent": test.o2_percent or 0.5,
        "nox_ppm": test.nox_ppm or 30,
        "lambda_value": test.lambda_value or 1.0,
        "smoke_opacity": test.smoke_opacity or 5,
        "exhaust_temp": test.exhaust_temp or 350,
        "engine_rpm": test.engine_rpm or 800,
        "air_fuel_ratio": test.air_fuel_ratio or 14.7,
        "oil_temp": test.oil_temp or 95,
        "coolant_temp": test.coolant_temp or 90,
        "ambient_temp": test.ambient_temp or 25,
        "relative_humidity": test.relative_humidity or 55,
        "engine_load": test.engine_load or 22,
        "throttle_position": test.throttle_position or 5,
        "fuel_consumption": test.fuel_consumption or 1.2,
        "fuel_pressure": test.fuel_pressure or 350,
        "turbo_pressure": test.turbo_pressure,
        "o2_sensor_reading": test.o2_sensor_reading or 0.45,
        "catalytic_efficiency": test.catalytic_efficiency or 96,
        "maf_sensor": test.maf_sensor or 15,
        "map_sensor": test.map_sensor or 35,
        "battery_voltage": test.battery_voltage or 13.8,
        "engine_running_time": test.engine_running_time or 2500,
    }

    vehicle_data = {
        "engine_capacity": vehicle.engine_capacity,
        "mileage": vehicle.mileage,
        "vehicle_age": max(0, 2026 - vehicle.year),
        "fuel_type": vehicle.fuel_type,
        "year": vehicle.year,
        "has_turbo": vehicle.turbo,
    }

    # Run prediction
    pipeline = get_pipeline()
    ml_result = pipeline.predict(emission_data, vehicle_data)

    # Save prediction to database
    prediction_id = generate_uuid()
    prediction = Prediction(
        id=prediction_id,
        vehicle_id=vehicle.id,
        emission_test_id=test.id,
        health_score=ml_result.get("health_score", 70),
        health_classification=ml_result.get("health_classification", "Moderate"),
        health_confidence=ml_result.get("confidence", 0.7),
        emission_compliance=ml_result.get("emission_compliance", "Warning"),
        emission_details=json.dumps(ml_result.get("emission_details", {}), default=str),
        detected_faults=json.dumps(ml_result.get("detected_faults", []), default=str),
        fault_count=ml_result.get("fault_count", 0),
        primary_fault=ml_result.get("primary_fault"),
        primary_fault_probability=ml_result.get("primary_fault_probability"),
        remaining_life_km=ml_result.get("remaining_life_km"),
        km_to_maintenance=ml_result.get("km_to_maintenance"),
        km_to_major_repair=ml_result.get("km_to_major_repair"),
        breakdown_probability=ml_result.get("breakdown_probability"),
        forecast_30d=json.dumps(ml_result.get("forecasts", [{}])[0] if ml_result.get("forecasts") else {}, default=str),
        forecast_90d=json.dumps(ml_result.get("forecasts", [{}, {}])[1] if len(ml_result.get("forecasts", [])) > 1 else {}, default=str),
        forecast_180d=json.dumps(ml_result.get("forecasts", [{}, {}, {}])[2] if len(ml_result.get("forecasts", [])) > 2 else {}, default=str),
        forecast_365d=json.dumps(ml_result.get("forecasts", [{}, {}, {}, {}])[3] if len(ml_result.get("forecasts", [])) > 3 else {}, default=str),
        estimated_repair_cost_min=ml_result.get("estimated_repair_cost_min"),
        estimated_repair_cost_max=ml_result.get("estimated_repair_cost_max"),
        risk_level=ml_result.get("risk_level", "Medium"),
        urgency_level=ml_result.get("urgency_level", "Medium"),
        fuel_efficiency_rating=ml_result.get("fuel_efficiency_rating"),
        environmental_impact_score=ml_result.get("environmental_impact_score"),
        emission_rating=ml_result.get("emission_rating"),
        shap_values=json.dumps(ml_result.get("shap_values", {}), default=str),
        feature_importance=json.dumps(ml_result.get("feature_importance", {}), default=str),
        explanation_text=ml_result.get("explanation_text", ""),
        recommendations=json.dumps(ml_result.get("recommendations", []), default=str),
        maintenance_schedule=json.dumps(ml_result.get("maintenance_schedule", []), default=str),
        model_version="1.0.0",
        model_type=ml_result.get("model_used", "rule_based"),
        overall_confidence=ml_result.get("overall_confidence", 0.7),
    )
    db.add(prediction)
    await db.flush()

    return AnalysisResponse(
        prediction_id=prediction_id,
        vehicle_id=str(vehicle.id),
        emission_test_id=str(test.id),
        health_score=ml_result.get("health_score", 70),
        health_classification=ml_result.get("health_classification", "Moderate"),
        health_confidence=ml_result.get("confidence", 0.7),
        emission_compliance=ml_result.get("emission_compliance", "Warning"),
        emission_details=ml_result.get("emission_details", {}),
        detected_faults=ml_result.get("detected_faults", []),
        fault_count=ml_result.get("fault_count", 0),
        primary_fault=ml_result.get("primary_fault"),
        primary_fault_probability=ml_result.get("primary_fault_probability"),
        remaining_life_km=ml_result.get("remaining_life_km"),
        km_to_maintenance=ml_result.get("km_to_maintenance"),
        km_to_major_repair=ml_result.get("km_to_major_repair"),
        breakdown_probability=ml_result.get("breakdown_probability"),
        forecasts=ml_result.get("forecasts", []),
        estimated_repair_cost_min=ml_result.get("estimated_repair_cost_min"),
        estimated_repair_cost_max=ml_result.get("estimated_repair_cost_max"),
        risk_level=ml_result.get("risk_level", "Medium"),
        urgency_level=ml_result.get("urgency_level", "Medium"),
        fuel_efficiency_rating=ml_result.get("fuel_efficiency_rating"),
        environmental_impact_score=ml_result.get("environmental_impact_score"),
        emission_rating=ml_result.get("emission_rating"),
        feature_importance=ml_result.get("feature_importance"),
        explanation_text=ml_result.get("explanation_text"),
        recommendations=ml_result.get("recommendations", []),
        maintenance_schedule=ml_result.get("maintenance_schedule", []),
        overall_confidence=ml_result.get("overall_confidence", 0.7),
        model_version="1.0.0",
        analyzed_at=utc_now(),
    )


@router.post("/predict-direct", response_model=ManualBikePredictionResponse)
@router.post("/predict-manual", response_model=ManualBikePredictionResponse)
async def predict_direct(data: ManualBikePredictionRequest):
    """
    Run direct ML engine health & emission prediction on manual motorbike data.
    Does not require user authentication or pre-existing database vehicle records.
    """
    # Enforce petrol fuel type
    if data.fuel_type and data.fuel_type.lower() != "petrol":
        raise HTTPException(
            status_code=400,
            detail=f"PredictV only supports petrol motorbikes. Received fuel_type='{data.fuel_type}'.",
        )

    pipeline = get_pipeline()

    emission_data = {
        "co_percent": data.co_percent,
        "co2_percent": data.co2_percent,
        "hc_ppm": data.hc_ppm,
        "o2_percent": data.o2_percent,
        "nox_ppm": data.nox_ppm,
        "lambda_value": data.lambda_value,
        "smoke_opacity": data.smoke_opacity,
        "engine_temperature_C": data.engine_temperature_c,
        "engine_rpm": data.engine_rpm,
        "fuel_consumption": data.fuel_consumption,
    }

    vehicle_data = {
        "brand": data.brand,
        "model": data.model,
        "year": data.year,
        "engine_cc": data.engine_cc,
        "mileage": data.mileage_km,
        "vehicle_age": max(0, 2026 - data.year),
        "fuel_type": data.fuel_type,
        "oil_condition": data.oil_condition,
        "catalytic_converter": data.catalytic_converter,
        "transmission": data.transmission,
    }

    ml_result = pipeline.predict(emission_data, vehicle_data)

    rem_km = ml_result.get("remaining_life_km")
    rem_months = round(rem_km / 500, 1) if rem_km else None

    return ManualBikePredictionResponse(
        prediction_id=generate_uuid(),
        bike_summary={
            "brand": data.brand,
            "model": data.model,
            "year": data.year,
            "engine_cc": data.engine_cc,
            "mileage_km": data.mileage_km,
            "fuel_type": data.fuel_type,
            "oil_condition": data.oil_condition,
            "catalytic_converter": data.catalytic_converter,
            "transmission": data.transmission,
            "registration_number": data.registration_number,
        },
        health_score=ml_result.get("health_score", 70.0),
        health_classification=ml_result.get("health_classification", "Moderate"),
        health_confidence=ml_result.get("confidence", 0.85),
        emission_compliance=ml_result.get("emission_compliance", "Warning"),
        emission_details=ml_result.get("emission_details", {}),
        detected_faults=ml_result.get("detected_faults", []),
        fault_count=ml_result.get("fault_count", 0),
        primary_fault=ml_result.get("primary_fault"),
        primary_fault_probability=ml_result.get("primary_fault_probability"),
        remaining_life_km=rem_km,
        remaining_life_months=rem_months,
        km_to_maintenance=ml_result.get("km_to_maintenance"),
        km_to_major_repair=ml_result.get("km_to_major_repair"),
        breakdown_probability=ml_result.get("breakdown_probability"),
        forecasts=ml_result.get("forecasts", []),
        estimated_repair_cost_min=ml_result.get("estimated_repair_cost_min"),
        estimated_repair_cost_max=ml_result.get("estimated_repair_cost_max"),
        risk_level=ml_result.get("risk_level", "Medium"),
        urgency_level=ml_result.get("urgency_level", "Medium"),
        fuel_efficiency_rating=ml_result.get("fuel_efficiency_rating"),
        environmental_impact_score=ml_result.get("environmental_impact_score"),
        emission_rating=ml_result.get("emission_rating"),
        feature_importance=ml_result.get("feature_importance"),
        explanation_text=ml_result.get("explanation_text"),
        recommendations=ml_result.get("recommendations", []),
        maintenance_schedule=ml_result.get("maintenance_schedule", []),
        overall_confidence=ml_result.get("overall_confidence", 0.85),
        model_used=ml_result.get("model_used", "CatBoost + Random Forest + MultiOutput + LightGBM"),
        analyzed_at=utc_now(),
    )


@router.post("/upload-csv", response_model=FileUploadResponse)
async def upload_csv(
    vehicle_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a CSV file with emission test data."""
    if not file.filename or not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be CSV or Excel format")

    content = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
    else:
        df = pd.read_excel(io.BytesIO(content))

    # Map columns to our schema
    column_mapping = {
        "co": "co_percent", "co%": "co_percent", "co_percent": "co_percent",
        "co2": "co2_percent", "co2%": "co2_percent",
        "hc": "hc_ppm", "hc_ppm": "hc_ppm",
        "o2": "o2_percent", "o2%": "o2_percent",
        "nox": "nox_ppm", "nox_ppm": "nox_ppm",
        "lambda": "lambda_value", "lambda_value": "lambda_value",
        "smoke": "smoke_opacity", "smoke_opacity": "smoke_opacity",
        "rpm": "engine_rpm", "engine_rpm": "engine_rpm",
    }
    df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)

    test_ids = []
    for _, row in df.iterrows():
        test_data = {col: row[col] for col in row.index if col in EmissionTestCreate.model_fields and pd.notna(row[col])}
        test = EmissionTest(
            id=generate_uuid(),
            vehicle_id=vehicle_id,
            **test_data,
        )
        db.add(test)
        test_ids.append(test.id)

    await db.flush()

    return FileUploadResponse(
        filename=file.filename,
        records_parsed=len(test_ids),
        emission_test_ids=test_ids,
        message=f"Successfully imported {len(test_ids)} emission test records",
    )


@router.get("/history/{vehicle_id}")
async def get_emission_history(
    vehicle_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get emission test history for a vehicle."""
    result = await db.execute(
        select(EmissionTest)
        .where(EmissionTest.vehicle_id == vehicle_id)
        .order_by(EmissionTest.tested_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tests = result.scalars().all()
    return [EmissionTestResponse.model_validate(t) for t in tests]
