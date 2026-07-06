from typing import Optional
"""
Maintenance Record ORM Model.

Stores maintenance history and scheduled maintenance for vehicles.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[Optional[str]] = mapped_column(String(36), primary_key=True)
    vehicle_id: Mapped[str] = mapped_column()
        String(36), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Maintenance Details
    maintenance_type: Mapped[str] = mapped_column(String(100), nullable=False)  # scheduled, repair, recall
    category: Mapped[str] = mapped_column(String(100), nullable=True)  # engine, brakes, electrical, etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=False)
    parts_replaced: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list

    # Cost
    labor_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    parts_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), default="USD")

    # Mileage
    mileage_at_service: Mapped[float] = mapped_column(Float, nullable=True)
    next_service_mileage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Service Provider
    service_provider: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    technician: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    is_completed: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=True)  # low, medium, high, critical

    # Dates
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_service_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column()
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column()
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_records")

    @property
    def total_cost_calculated(self) -> float:
        return (self.labor_cost or 0) + (self.parts_cost or 0)

    def __repr__(self) -> str:
        return f"<MaintenanceRecord(id={self.id}, type={self.maintenance_type})>"
