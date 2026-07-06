"""
Vehicle API Routes.

CRUD operations for vehicles.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.schemas import VehicleCreate, VehicleListResponse, VehicleResponse, VehicleUpdate
from app.utils.helpers import generate_uuid

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("/", response_model=VehicleListResponse)
async def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List vehicles for the current user (or all for admin)."""
    query = select(Vehicle)
    count_query = select(func.count(Vehicle.id))

    if user.role != "admin":
        query = query.where(Vehicle.owner_id == user.id)
        count_query = count_query.where(Vehicle.owner_id == user.id)

    if search:
        search_filter = (
            Vehicle.brand.ilike(f"%{search}%") |
            Vehicle.model.ilike(f"%{search}%") |
            Vehicle.vin.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(Vehicle.created_at.desc()).offset(skip).limit(limit))
    vehicles = result.scalars().all()

    return VehicleListResponse(
        vehicles=[VehicleResponse.model_validate(v) for v in vehicles],
        total=total,
    )


@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    data: VehicleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new vehicle."""
    # Check VIN uniqueness
    if data.vin:
        existing = await db.execute(select(Vehicle).where(Vehicle.vin == data.vin))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="VIN already registered")

    vehicle = Vehicle(
        id=generate_uuid(),
        owner_id=user.id,
        **data.model_dump(),
    )
    db.add(vehicle)
    await db.flush()
    await db.refresh(vehicle)
    return vehicle


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single vehicle by ID."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if user.role != "admin" and vehicle.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    data: VehicleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a vehicle."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if user.role != "admin" and vehicle.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vehicle, key, value)

    await db.flush()
    await db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a vehicle."""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if user.role != "admin" and vehicle.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(vehicle)
