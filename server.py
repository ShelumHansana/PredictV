"""
PredictV Web Application Entrypoint
"""
import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' package inside backend is imported
backend_path = str(Path(__file__).resolve().parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
