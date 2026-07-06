from typing import Optional
"""
Report ORM Model.

Stores generated diagnostic report metadata and file paths.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[Optional[str]] = mapped_column(String(36), primary_key=True)
    vehicle_id: Mapped[str] = mapped_column()
        String(36), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generated_by: Mapped[str] = mapped_column()
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    

    # Report Details
    report_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False, default="full_diagnostic")
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # File Storage
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # bytes
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Summary Data
    health_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    compliance_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fault_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    overall_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Technician Notes
    technician_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Report Content Cache (JSON)
    report_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column()
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    vehicle = relationship("Vehicle", back_populates="reports")
    generated_by_user = relationship("User", back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, number={self.report_number})>"
