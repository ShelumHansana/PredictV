"""Request and response shapes for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.features import SYMPTOM_IDS
from app.knowledge import FAULTS

FAULT_IDS = {f["id"] for f in FAULTS}


class Bike(BaseModel):
    name: Optional[str] = Field(None, max_length=80)
    mileage_km: Optional[float] = Field(None, ge=0, le=1_000_000)

    @field_validator("name")
    @classmethod
    def tidy_name(cls, v: Optional[str]) -> Optional[str]:
        v = (v or "").strip()
        return v or None


class ServiceKm(BaseModel):
    """Kilometres ridden since each job was last done. Empty when not known."""
    oil: Optional[float] = Field(None, ge=0, le=500_000)
    air_filter: Optional[float] = Field(None, ge=0, le=500_000)
    spark_plug: Optional[float] = Field(None, ge=0, le=500_000)


class EmissionReport(BaseModel):
    """Values from an emission test report. CO and HC go together; the rest are optional."""
    co_percent: Optional[float] = Field(None, ge=0, le=20)
    hc_ppm: Optional[float] = Field(None, ge=0, le=30_000)
    co2_percent: Optional[float] = Field(None, ge=0, le=20)
    o2_percent: Optional[float] = Field(None, ge=0, le=25)
    lambda_value: Optional[float] = Field(None, ge=0.3, le=3)


class DiagnoseRequest(BaseModel):
    bike: Bike = Bike()
    symptoms: list[str] = Field(default_factory=list, max_length=40)
    service: ServiceKm = ServiceKm()
    emission: EmissionReport = EmissionReport()

    @field_validator("symptoms")
    @classmethod
    def known_symptoms(cls, v: list[str]) -> list[str]:
        unknown = [s for s in v if s not in SYMPTOM_IDS]
        if unknown:
            raise ValueError(f"Unknown symptom id(s): {unknown}")
        return sorted(set(v))


class FeedbackIn(BaseModel):
    confirmed_fault: str = Field(..., max_length=40)
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("confirmed_fault")
    @classmethod
    def known_fault(cls, v: str) -> str:
        if v not in FAULT_IDS | {"other", "none"}:
            raise ValueError("Unknown fault id")
        return v


class FeedbackOut(BaseModel):
    confirmed_fault: str
    note: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class DiagnosisSummary(BaseModel):
    id: str
    created_at: datetime
    bike_name: Optional[str] = None
    overall: str
    top_fault: Optional[str] = None
    fault_count: int
    has_feedback: bool


class DiagnosisOut(BaseModel):
    id: str
    created_at: datetime
    bike_name: Optional[str] = None
    overall: str
    answers: dict[str, Any]
    result: dict[str, Any]
    feedback: Optional[FeedbackOut] = None
    model_config = {"from_attributes": True}
