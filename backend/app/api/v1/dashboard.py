"""
Dashboard API Routes.

Statistics, trends, and aggregated data for the dashboard.
"""

import json
from collections import Counter
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.emission_test import EmissionTest
from app.models.prediction import Prediction
from app.models.report import Report
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated dashboard statistics."""
    is_admin = user.role == "admin"

    # Vehicle count
    vq = select(func.count(Vehicle.id))
    if not is_admin:
        vq = vq.where(Vehicle.owner_id == user.id)
    total_vehicles = (await db.execute(vq)).scalar() or 0

    # Get user's vehicle IDs for filtering
    if not is_admin:
        vids_result = await db.execute(select(Vehicle.id).where(Vehicle.owner_id == user.id))
        vehicle_ids = [v[0] for v in vids_result.all()]
    else:
        vehicle_ids = None  # No filter needed for admin

    # Prediction count
    pq = select(func.count(Prediction.id))
    if vehicle_ids is not None:
        pq = pq.where(Prediction.vehicle_id.in_(vehicle_ids)) if vehicle_ids else pq.where(False)
    total_analyses = (await db.execute(pq)).scalar() or 0

    # Report count
    rq = select(func.count(Report.id))
    if vehicle_ids is not None:
        rq = rq.where(Report.vehicle_id.in_(vehicle_ids)) if vehicle_ids else rq.where(False)
    total_reports = (await db.execute(rq)).scalar() or 0

    # Average health score
    hq = select(func.avg(Prediction.health_score))
    if vehicle_ids is not None:
        hq = hq.where(Prediction.vehicle_id.in_(vehicle_ids)) if vehicle_ids else hq.where(False)
    avg_health = (await db.execute(hq)).scalar() or 0

    # Compliance pass rate
    pass_q = select(func.count(Prediction.id)).where(Prediction.emission_compliance == "Pass")
    if vehicle_ids is not None:
        pass_q = pass_q.where(Prediction.vehicle_id.in_(vehicle_ids)) if vehicle_ids else pass_q.where(False)
    pass_count = (await db.execute(pass_q)).scalar() or 0
    compliance_rate = (pass_count / total_analyses * 100) if total_analyses > 0 else 0

    # Critical vehicles
    crit_q = select(func.count(Prediction.id)).where(
        Prediction.health_score < 30
    )
    if vehicle_ids is not None:
        crit_q = crit_q.where(Prediction.vehicle_id.in_(vehicle_ids)) if vehicle_ids else crit_q.where(False)
    critical = (await db.execute(crit_q)).scalar() or 0

    # Recent analyses
    recent_q = select(Prediction).order_by(Prediction.created_at.desc()).limit(10)
    if vehicle_ids is not None:
        recent_q = recent_q.where(Prediction.vehicle_id.in_(vehicle_ids)) if vehicle_ids else recent_q.where(False)
    recent_result = await db.execute(recent_q)
    recent_predictions = recent_result.scalars().all()

    recent_analyses = [
        {
            "id": p.id,
            "vehicle_id": p.vehicle_id,
            "health_score": p.health_score,
            "health_classification": p.health_classification,
            "emission_compliance": p.emission_compliance,
            "fault_count": p.fault_count,
            "risk_level": p.risk_level,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in recent_predictions
    ]

    # Health distribution
    health_dist = {"Excellent": 0, "Good": 0, "Moderate": 0, "Poor": 0, "Critical": 0}
    for p in recent_predictions:
        if p.health_classification in health_dist:
            health_dist[p.health_classification] += 1

    # Fault distribution
    fault_dist: dict = {}
    for p in recent_predictions:
        if p.detected_faults:
            try:
                faults = json.loads(p.detected_faults) if isinstance(p.detected_faults, str) else p.detected_faults
                for f in faults:
                    name = f.get("fault", "Unknown") if isinstance(f, dict) else str(f)
                    fault_dist[name] = fault_dist.get(name, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass

    return DashboardStats(
        total_vehicles=total_vehicles,
        total_analyses=total_analyses,
        total_reports=total_reports,
        avg_health_score=round(avg_health, 1),
        compliance_pass_rate=round(compliance_rate, 1),
        critical_vehicles=critical,
        recent_analyses=recent_analyses,
        health_distribution=health_dist,
        fault_distribution=dict(sorted(fault_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
        monthly_trends=[],
    )


@router.get("/trends")
async def get_trends(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get trend data for dashboard charts."""
    is_admin = user.role == "admin"

    query = select(Prediction).order_by(Prediction.created_at.desc()).limit(100)
    if not is_admin:
        vids_result = await db.execute(select(Vehicle.id).where(Vehicle.owner_id == user.id))
        vehicle_ids = [v[0] for v in vids_result.all()]
        if vehicle_ids:
            query = query.where(Prediction.vehicle_id.in_(vehicle_ids))

    result = await db.execute(query)
    predictions = result.scalars().all()

    # Build trend data
    health_trend = []
    compliance_trend = []
    for p in reversed(predictions):
        date_str = p.created_at.strftime("%Y-%m-%d") if p.created_at else ""
        health_trend.append({"date": date_str, "value": p.health_score})
        compliance_trend.append({
            "date": date_str,
            "value": 1 if p.emission_compliance == "Pass" else 0,
        })

    return {
        "health_trend": health_trend,
        "compliance_trend": compliance_trend,
    }
