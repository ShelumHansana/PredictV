"""
PredictV — AI Petrol Motorbike Exhaust Analysis & Engine Health Prediction System.

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from pathlib import Path


from fastapi import FastAPI, HTTPException


from fastapi.middleware.cors import CORSMiddleware


from fastapi.responses import FileResponse, ORJSONResponse

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
    print("[INFO] Starting PredictV...")
    await init_db()
    print("[OK] Database initialized")

    # Try to load ML models
    try:
        from app.api.v1.emissions import get_pipeline
        pipeline = get_pipeline()
        if pipeline.is_loaded:
            print("[OK] ML models loaded successfully")
        else:
            print("[WARN] ML models not found — using rule-based fallback")
    except Exception as e:
        print(f"[WARN] ML model loading skipped: {e}")

    yield

    # Shutdown
    await close_db()
    print("[INFO] PredictV shutdown complete")


app = FastAPI(
    title="PredictV API",
    description=(
        "AI Petrol Motorbike Exhaust Analysis & Engine Health Prediction System.\n\n"
        "Analyzes petrol motorbike exhaust emissions and predicts engine health, faults, "
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


# Serve frontend
_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@app.get("/", tags=["Root"])
async def root():
    """Serve the PredictV frontend."""
    index = _FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
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


@app.get("/{filename:path}", include_in_schema=False)
async def serve_static(filename: str):
    """Serve static frontend assets (css, js, images)."""
    file_path = _FRONTEND_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    raise HTTPException(status_code=404, detail="Not Found")
