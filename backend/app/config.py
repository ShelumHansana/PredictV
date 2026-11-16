"""Settings, read from environment variables (all optional)."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

DATA_DIR = BACKEND_DIR / "data"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'predictv.db').as_posix()}")

# The built React app. Present after `npm run build`; in development Vite serves the frontend instead.
FRONTEND_DIST = PROJECT_DIR / "frontend" / "dist"

# Set COOKIE_SECURE=1 when the site is served over https.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
COOKIE_NAME = "pv_client"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365

# Extra origins allowed to call the API (comma separated). Not needed when the
# frontend is served by this app or through the Vite dev proxy.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

HISTORY_LIMIT = 50          # checks kept per browser
