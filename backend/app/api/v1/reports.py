"""
Report API Routes.

Generate diagnostic PDF reports and manage report records.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.prediction import Prediction
from app.models.report import Report
from app.models.user import User
from app.models.vehicle import Vehicle
from app.reports.generator import ReportGenerator
from app.schemas.schemas import ReportGenerateRequest, ReportListResponse, ReportResponse
from app.utils.helpers import generate_uuid

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    data: ReportGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a professional PDF diagnostic report."""
    # Get prediction
    result = await db.execute(select(Prediction).where(Prediction.id == data.prediction_id))
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    # Get vehicle
    result = await db.execute(select(Vehicle).where(Vehicle.id == prediction.vehicle_id))
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Generate report number
    count = await db.execute(select(func.count(Report.id)))
    report_num = f"PV-{(count.scalar() or 0) + 1:06d}"

    # Generate PDF
    report_dir = settings.report_path
    file_name = f"{report_num}.pdf"
    file_path = report_dir / file_name

    def safe_json(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return []
        return val or []

    report_data = {
        "report_number": report_num,
        "vehicle": {
            "brand": vehicle.brand,
            "model": vehicle.model,
            "year": vehicle.year,
            "engine_capacity": vehicle.engine_capacity,
            "fuel_type": vehicle.fuel_type,
            "mileage": vehicle.mileage,
            "vin": vehicle.vin or "N/A",
        },
        "health_score": prediction.health_score,
        "health_classification": prediction.health_classification,
        "emission_compliance": prediction.emission_compliance,
        "detected_faults": safe_json(prediction.detected_faults),
        "recommendations": safe_json(prediction.recommendations),
        "maintenance_schedule": safe_json(prediction.maintenance_schedule),
        "forecasts": [
            safe_json(prediction.forecast_30d),
            safe_json(prediction.forecast_90d),
            safe_json(prediction.forecast_180d),
            safe_json(prediction.forecast_365d),
        ],
        "remaining_life_km": prediction.remaining_life_km,
        "km_to_maintenance": prediction.km_to_maintenance,
        "breakdown_probability": prediction.breakdown_probability,
        "estimated_repair_cost_min": prediction.estimated_repair_cost_min,
        "estimated_repair_cost_max": prediction.estimated_repair_cost_max,
        "risk_level": prediction.risk_level,
        "urgency_level": prediction.urgency_level,
        "fuel_efficiency_rating": prediction.fuel_efficiency_rating,
        "environmental_impact_score": prediction.environmental_impact_score,
        "emission_rating": prediction.emission_rating,
        "overall_confidence": prediction.overall_confidence,
        "feature_importance": safe_json(prediction.feature_importance),
        "explanation_text": prediction.explanation_text,
        "technician_notes": data.technician_notes or "",
    }

    generator = ReportGenerator()
    generator.generate(report_data, str(file_path))

    # Save report record
    report = Report(
        id=generate_uuid(),
        vehicle_id=vehicle.id,
        generated_by=user.id,
        report_number=report_num,
        report_type=data.report_type,
        title=f"Diagnostic Report — {vehicle.brand} {vehicle.model} ({vehicle.year})",
        file_path=str(file_path),
        file_size=file_path.stat().st_size if file_path.exists() else 0,
        health_score=prediction.health_score,
        compliance_status=prediction.emission_compliance,
        fault_count=prediction.fault_count,
        risk_level=prediction.risk_level,
        overall_confidence=prediction.overall_confidence,
        technician_notes=data.technician_notes,
        report_data=json.dumps(report_data, default=str),
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a generated PDF report."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = Path(report.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on server")

    return FileResponse(
        path=str(file_path),
        filename=f"{report.report_number}.pdf",
        media_type="application/pdf",
    )


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all reports for the current user."""
    query = select(Report)
    if user.role != "admin":
        vehicle_ids = await db.execute(
            select(Vehicle.id).where(Vehicle.owner_id == user.id)
        )
        vids = [v[0] for v in vehicle_ids.all()]
        if not vids:
            return ReportListResponse(reports=[], total=0)
        query = query.where(Report.vehicle_id.in_(vids))

    result = await db.execute(query.order_by(Report.created_at.desc()))
    reports = result.scalars().all()
    return ReportListResponse(
        reports=[ReportResponse.model_validate(r) for r in reports],
        total=len(reports),
    )
