"""Models package — imports all ORM models for Alembic and session access."""

from app.models.emission_test import EmissionTest
from app.models.maintenance import MaintenanceRecord
from app.models.prediction import Prediction
from app.models.report import Report
from app.models.user import User
from app.models.vehicle import Vehicle

__all__ = [
    "User",
    "Vehicle",
    "EmissionTest",
    "Prediction",
    "Report",
    "MaintenanceRecord",
]
