from typing import Optional
"""
Emission Test ORM Model.

Stores complete emission test data with all 30+ sensor readings.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmissionTest(Base):
    __tablename__ = "emission_tests"

    id: Mapped[Optional[str]] = mapped_column(String(36), primary_key=True)
    vehicle_id: Mapped[str] = mapped_column()
        String(36), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Emission Values ──────────────────────────
    co_percent: Mapped[float] = mapped_column(Float, nullable=True)  # CO (%)
    co2_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # CO₂ (%)
    hc_ppm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # HC (ppm)
    o2_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # O₂ (%)
    nox_ppm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # NOx (ppm)
    lambda_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Lambda
    smoke_opacity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Smoke Opacity (%)

    # ── Engine Sensor Data ───────────────────────
    exhaust_temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Exhaust Temp (°C)
    engine_rpm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Engine RPM
    air_fuel_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Air-Fuel Ratio
    oil_temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Oil Temp (°C)
    coolant_temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Coolant Temp (°C)

    # ── Environmental Data ───────────────────────
    ambient_temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Ambient Temp (°C)
    relative_humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Relative Humidity (%)

    # ── Performance Data ─────────────────────────
    engine_load: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Engine Load (%)
    throttle_position: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Throttle Position (%)
    fuel_consumption: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Fuel Consumption (L/h)
    fuel_pressure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Fuel Pressure (kPa)
    turbo_pressure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Turbo Pressure (bar)

    # ── Sensor Readings ──────────────────────────
    o2_sensor_reading: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # O₂ Sensor (V)
    catalytic_efficiency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Cat. Efficiency (%)
    maf_sensor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # MAF (g/s)
    map_sensor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # MAP (kPa)
    battery_voltage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Battery (V)
    engine_running_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Running Time (hours)

    # ── Additional OBD-II Data ───────────────────
    obd_dtc_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Stored DTC codes (JSON)
    additional_sensors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Additional OBD data (JSON)

    # ── Test Metadata ────────────────────────────
    test_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # idle, loaded, free_rev
    test_station: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    technician_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mileage_at_test: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    tested_at: Mapped[datetime] = mapped_column()
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column()
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    vehicle = relationship("Vehicle", back_populates="emission_tests")
    predictions = relationship("Prediction", back_populates="emission_test", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<EmissionTest(id={self.id}, vehicle_id={self.vehicle_id}, tested_at={self.tested_at})>"
