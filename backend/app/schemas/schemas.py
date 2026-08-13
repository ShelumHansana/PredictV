"""
Pydantic Schemas for all API request/response models.

Organized by domain: auth, vehicle (petrol motorbike), emission, prediction, report, user.
"""

from datetime import datetime
from typing import Any, Optional


from pydantic import BaseModel, Field

# ══════════════════════════════════════════════
# Authentication Schemas
# ══════════════════════════════════════════════

class UserRegister(BaseModel):
    email: str = Field(..., examples=["tech@predictv.com"])
    username: str = Field(..., min_length=3, max_length=100, examples=["john_tech"])
    password: str = Field(..., min_length=8, examples=["SecurePass123!"])
    full_name: str = Field(..., examples=["John Smith"])
    role: str = Field(default="owner", examples=["technician"])
    phone: Optional[str] = Field(None, examples=["+1-555-0123"])
    company: Optional[str] = Field(None, examples=["AutoCare Diagnostics"])


class UserLogin(BaseModel):
    username: str = Field(..., examples=["john_tech"])
    password: str = Field(..., examples=["SecurePass123!"])


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: str
    phone: Optional[str] = None
    company: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None


# ══════════════════════════════════════════════
# Vehicle Schemas
# ══════════════════════════════════════════════

class VehicleCreate(BaseModel):
    brand: str = Field(..., examples=["Honda"])
    model: str = Field(..., examples=["CB Hornet 160R"])
    year: int = Field(..., ge=1900, le=2030, examples=[2022])
    engine_capacity: float = Field(..., gt=0, examples=[0.16])
    fuel_type: str = Field(default="petrol", examples=["petrol"], description="Only petrol is supported")
    vehicle_type: str = Field(default="motorbike", examples=["motorbike"], description="Only motorbikes are supported")
    mileage: float = Field(default=0, ge=0, examples=[25000])
    vin: Optional[str] = Field(None, max_length=17, examples=["1HGBH41JXMN109186"])
    cylinders: Optional[int] = Field(None, examples=[1])
    horsepower: Optional[float] = Field(None, examples=[15.6])
    transmission: Optional[str] = Field(None, examples=["manual"])
    turbo: bool = Field(default=False)
    registration_number: Optional[str] = Field(None, examples=["ABC-1234"])
    service_history_notes: Optional[str] = None
    notes: Optional[str] = None


class VehicleUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    engine_capacity: Optional[float] = None
    fuel_type: Optional[str] = None
    mileage: Optional[float] = None
    vin: Optional[str] = None
    service_history_notes: Optional[str] = None
    notes: Optional[str] = None


class VehicleResponse(BaseModel):
    id: str
    owner_id: str
    brand: str
    model: str
    year: int
    engine_capacity: float
    fuel_type: str
    vehicle_type: str = "motorbike"
    mileage: float
    vin: Optional[str] = None
    cylinders: Optional[int] = None
    horsepower: Optional[float] = None
    transmission: Optional[str] = None
    turbo: bool
    registration_number: Optional[str] = None
    last_service_date: Optional[datetime] = None
    last_service_mileage: Optional[float] = None
    service_history_notes: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VehicleListResponse(BaseModel):
    vehicles: list[VehicleResponse]
    total: int


# ══════════════════════════════════════════════
# Emission Test Schemas
# ══════════════════════════════════════════════

class EmissionTestCreate(BaseModel):
    vehicle_id: str

    # Emission Values
    co_percent: Optional[float] = Field(None, ge=0, examples=[0.25])
    co2_percent: Optional[float] = Field(None, ge=0, examples=[14.2])
    hc_ppm: Optional[float] = Field(None, ge=0, examples=[85])
    o2_percent: Optional[float] = Field(None, ge=0, examples=[0.8])
    nox_ppm: Optional[float] = Field(None, ge=0, examples=[45])
    lambda_value: Optional[float] = Field(None, gt=0, examples=[1.01])
    smoke_opacity: Optional[float] = Field(None, ge=0, le=100, examples=[5])

    # Engine Sensors
    exhaust_temp: Optional[float] = Field(None, examples=[320])
    engine_rpm: Optional[float] = Field(None, ge=0, examples=[800])
    air_fuel_ratio: Optional[float] = Field(None, examples=[14.7])
    oil_temp: Optional[float] = Field(None, examples=[95])
    coolant_temp: Optional[float] = Field(None, examples=[90])

    # Environment
    ambient_temp: Optional[float] = Field(None, examples=[25])
    relative_humidity: Optional[float] = Field(None, ge=0, le=100, examples=[55])

    # Performance
    engine_load: Optional[float] = Field(None, ge=0, le=100, examples=[22])
    throttle_position: Optional[float] = Field(None, ge=0, le=100, examples=[5])
    fuel_consumption: Optional[float] = Field(None, ge=0, examples=[1.2])
    fuel_pressure: Optional[float] = Field(None, ge=0, examples=[350])
    turbo_pressure: Optional[float] = Field(None, ge=0)

    # Sensors
    o2_sensor_reading: Optional[float] = Field(None, examples=[0.45])
    catalytic_efficiency: Optional[float] = Field(None, ge=0, le=100, examples=[96])
    maf_sensor: Optional[float] = Field(None, ge=0, examples=[15])
    map_sensor: Optional[float] = Field(None, ge=0, examples=[35])
    battery_voltage: Optional[float] = Field(None, examples=[13.8])
    engine_running_time: Optional[float] = Field(None, ge=0, examples=[2500])

    # Additional
    obd_dtc_codes: Optional[str] = None
    additional_sensors: Optional[str] = None
    test_type: Optional[str] = Field(None, examples=["idle"])
    test_station: Optional[str] = None
    technician_name: Optional[str] = None
    notes: Optional[str] = None
    mileage_at_test: Optional[float] = None


class EmissionTestResponse(BaseModel):
    id: str
    vehicle_id: str
    co_percent: Optional[float] = None
    co2_percent: Optional[float] = None
    hc_ppm: Optional[float] = None
    o2_percent: Optional[float] = None
    nox_ppm: Optional[float] = None
    lambda_value: Optional[float] = None
    smoke_opacity: Optional[float] = None
    exhaust_temp: Optional[float] = None
    engine_rpm: Optional[float] = None
    air_fuel_ratio: Optional[float] = None
    oil_temp: Optional[float] = None
    coolant_temp: Optional[float] = None
    ambient_temp: Optional[float] = None
    relative_humidity: Optional[float] = None
    engine_load: Optional[float] = None
    throttle_position: Optional[float] = None
    fuel_consumption: Optional[float] = None
    fuel_pressure: Optional[float] = None
    turbo_pressure: Optional[float] = None
    o2_sensor_reading: Optional[float] = None
    catalytic_efficiency: Optional[float] = None
    maf_sensor: Optional[float] = None
    map_sensor: Optional[float] = None
    battery_voltage: Optional[float] = None
    engine_running_time: Optional[float] = None
    obd_dtc_codes: Optional[str] = None
    additional_sensors: Optional[str] = None
    test_type: Optional[str] = None
    tested_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════
# Prediction / Analysis Schemas
# ══════════════════════════════════════════════

class FaultPrediction(BaseModel):
    fault: str
    probability: float
    severity: str
    estimated_repair_cost: float
    description: str


class ForecastPoint(BaseModel):
    horizon: str  # "30d", "90d", "180d", "1y"
    health_score: float
    emission_increase_pct: float
    fuel_efficiency_loss_pct: float
    maintenance_cost: float
    risk_score: float
    engine_degradation_pct: float


class AnalysisRequest(BaseModel):
    """Request body for running a full analysis on an emission test."""
    emission_test_id: str
    include_forecasts: bool = True
    include_explanations: bool = True


class AnalysisResponse(BaseModel):
    """Complete analysis result."""

    model_config = {"protected_namespaces": ()}

    prediction_id: str
    vehicle_id: str
    emission_test_id: str

    # Health
    health_score: float
    health_classification: str
    health_confidence: float

    # Compliance
    emission_compliance: str
    emission_details: dict[str, Any]

    # Faults
    detected_faults: list[FaultPrediction]
    fault_count: int
    primary_fault: Optional[str] = None
    primary_fault_probability: Optional[float] = None

    # RUL
    remaining_life_km: Optional[float] = None
    km_to_maintenance: Optional[float] = None
    km_to_major_repair: Optional[float] = None
    breakdown_probability: Optional[float] = None

    # Forecasts
    forecasts: list[ForecastPoint]

    # Derived
    estimated_repair_cost_min: Optional[float] = None
    estimated_repair_cost_max: Optional[float] = None
    risk_level: str
    urgency_level: str
    fuel_efficiency_rating: Optional[float] = None
    environmental_impact_score: Optional[float] = None
    emission_rating: Optional[str] = None

    # Explainability
    feature_importance: Optional[dict[str, float]] = None
    explanation_text: Optional[str] = None

    # Recommendations
    recommendations: list[dict[str, Any]]
    maintenance_schedule: list[dict[str, Any]]

    # Metadata
    overall_confidence: float
    model_version: Optional[str] = None
    analyzed_at: datetime


# ══════════════════════════════════════════════
# Report Schemas
# ══════════════════════════════════════════════

class ReportGenerateRequest(BaseModel):
    prediction_id: str
    technician_notes: Optional[str] = None
    report_type: str = Field(default="full_diagnostic", examples=["full_diagnostic"])


class ReportResponse(BaseModel):
    id: str
    vehicle_id: str
    report_number: str
    report_type: str
    title: str
    health_score: Optional[float] = None
    compliance_status: Optional[str] = None
    fault_count: Optional[int] = None
    risk_level: Optional[str] = None
    overall_confidence: Optional[float] = None
    technician_notes: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int


# ══════════════════════════════════════════════
# Dashboard Schemas
# ══════════════════════════════════════════════

class DashboardStats(BaseModel):
    total_vehicles: int
    total_analyses: int
    total_reports: int
    avg_health_score: float
    compliance_pass_rate: float
    critical_vehicles: int
    recent_analyses: list[dict[str, Any]]
    health_distribution: dict[str, int]
    fault_distribution: dict[str, int]
    monthly_trends: list[dict[str, Any]]


class TrendData(BaseModel):
    labels: list[str]
    datasets: list[dict[str, Any]]


# ══════════════════════════════════════════════
# Maintenance Schemas
# ══════════════════════════════════════════════

class MaintenanceCreate(BaseModel):
    vehicle_id: str
    maintenance_type: str = Field(..., examples=["scheduled"])
    category: Optional[str] = Field(None, examples=["engine"])
    description: str = Field(..., examples=["Oil change and filter replacement"])
    parts_replaced: Optional[str] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    total_cost: Optional[float] = None
    mileage_at_service: Optional[float] = None
    service_provider: Optional[str] = None
    technician: Optional[str] = None
    is_completed: bool = True
    priority: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: str
    vehicle_id: str
    maintenance_type: str
    category: Optional[str] = None
    description: str
    parts_replaced: Optional[str] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    total_cost: Optional[float] = None
    mileage_at_service: Optional[float] = None
    service_provider: Optional[str] = None
    technician: Optional[str] = None
    is_completed: bool
    is_scheduled: bool
    priority: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    next_service_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════
# File Upload Schemas
# ══════════════════════════════════════════════

class FileUploadResponse(BaseModel):
    filename: str
    records_parsed: int
    emission_test_ids: list[str]
    message: str


# Forward ref resolution
Token.model_rebuild()
