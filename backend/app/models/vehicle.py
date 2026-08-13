from typing import Optional
"""
Vehicle ORM Model (Petrol Motorbikes).

Stores petrol motorbike information including brand, model, engine specs, and service history.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.constants import FuelType


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[Optional[str]] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Vehicle Identification
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    vin: Mapped[str] = mapped_column(String(17), nullable=True, unique=True, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False, default="motorbike")

    # Engine Specifications
    engine_capacity: Mapped[Optional[float]] = mapped_column(Float, nullable=False)  # in liters
    fuel_type: Mapped[str] = mapped_column(
        Enum(FuelType, name="fuel_type"), nullable=False
    )
    cylinders: Mapped[int] = mapped_column(Integer, nullable=True)
    horsepower: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transmission: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    turbo: Mapped[Optional[bool]] = mapped_column(default=False)

    # Usage
    mileage: Mapped[float] = mapped_column(Float, nullable=False, default=0)  # in km
    registration_number: Mapped[str] = mapped_column(String(20), nullable=True)

    # Service History
    last_service_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_service_mileage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    service_history_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owner = relationship("User", back_populates="vehicles")
    emission_tests = relationship("EmissionTest", back_populates="vehicle", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="vehicle", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="vehicle", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle", cascade="all, delete-orphan")

    @property
    def display_name(self) -> str:
        return f"{self.year} {self.brand} {self.model}"

    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, name={self.display_name})>"
