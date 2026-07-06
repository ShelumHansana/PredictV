"""
PredictV — AI Vehicle Exhaust Analysis & Engine Health Prediction System.

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.emissions import router as emissions_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.reports import router as reports_router
from app.api.v1.users import router as users_router
from app.api.v1.vehicles import router as vehicles_router
from app.config import settings
from app.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    print("🚀 Starting PredictV...")
    await init_db()
    print("✅ Database initialized")

    # Try to load ML models
    try:
        from app.api.v1.emissions import get_pipeline
        pipeline = get_pipeline()
        if pipeline.is_loaded:
            print("✅ ML models loaded")
        else:
            print("⚠️  ML models not found — using rule-based predictions")
    except Exception as e:
        print(f"⚠️  ML model loading skipped: {e}")

    yield

    # Shutdown
    await close_db()
    print("👋 PredictV shutdown complete")


app = FastAPI(
    title="PredictV API",
    description=(
        "AI Vehicle Exhaust Analysis & Engine Health Prediction System.\n\n"
        "Analyzes vehicle exhaust emissions and predicts engine health, faults, "
        "remaining useful life, and future condition using machine learning."
    ),
    version=settings.APP_VERSION,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routes
API_PREFIX = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(vehicles_router, prefix=API_PREFIX)
app.include_router(emissions_router, prefix=API_PREFIX)
app.include_router(predictions_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """API root — health check."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
