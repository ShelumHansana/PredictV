"""
PredictV API (FastAPI).

    GET    /api/meta                       questions, fault texts, limits, model facts
    POST   /api/diagnoses                  run a check and save it
    GET    /api/diagnoses                  this browser's saved checks
    GET    /api/diagnoses/{id}             one saved check
    DELETE /api/diagnoses/{id}
    PUT    /api/diagnoses/{id}/feedback    what the mechanic actually found
    GET    /health

Development: `npm run dev` at the project root starts this and the React app.
Production:  `npm run build && npm start` - this app then also serves frontend/dist.
"""

from __future__ import annotations

import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS, FRONTEND_DIST
from app.db import init_db
from app.routers import diagnoses, meta
from app.services import mixture_model, symptom_model

# Some Windows machines report .js as text/plain, which stops browsers loading the app.
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="PredictV API", version="3.0.0", lifespan=lifespan)

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"],
    )

app.include_router(meta.router)
app.include_router(diagnoses.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "healthy", "mixture_model": mixture_model.ready, "symptom_model": symptom_model.ready}


# ── built frontend (production only) ─────────────────────────────────────────
if (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        """Serve a real file from dist if there is one, otherwise the React app (client-side routes)."""
        if path.startswith("api/"):
            raise HTTPException(404, "Not found")
        target = (FRONTEND_DIST / path).resolve()
        if path and target.is_file() and FRONTEND_DIST.resolve() in target.parents:
            return FileResponse(target)
        return FileResponse(FRONTEND_DIST / "index.html")
