import os
import sys
import shutil
import logging
from contextlib import asynccontextmanager

# Add the parent directory to sys.path so that 'from backend...' imports work 
# even when running uvicorn from inside the backend directory.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models.loader import ml_models, get_forecaster
from backend.routers import (
    scenario,
    upload,
    forecast,
    mitre,
    xai,
    soc,
    benchmark,
    report,
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    os.makedirs("scratch", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    logger.info("Loading ML models...")
    ml_models.load_models()
    logger.info("ML models loaded successfully. Server is ready.")
    yield
    # ── Shutdown ──
    if os.path.isdir("scratch"):
        shutil.rmtree("scratch", ignore_errors=True)
        logger.info("Cleaned up scratch directory.")
    logger.info("Server shutdown complete.")

app = FastAPI(
    title="Predictive Cyber Defense & SOC API",
    description="Backend API for AI-driven attack forecasting and SOC playbooks.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow CORS for Next.js frontend
frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(scenario.router, prefix="/api", tags=["scenario"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(forecast.router, prefix="/api", tags=["forecast"])
app.include_router(mitre.router, prefix="/api", tags=["mitre"])
app.include_router(xai.router, prefix="/api", tags=["xai"])
app.include_router(soc.router, prefix="/api", tags=["soc"])
app.include_router(benchmark.router, prefix="/api", tags=["benchmark"])
app.include_router(report.router, prefix="/api", tags=["report"])

@app.get("/healthz")
def healthz(forecaster=Depends(get_forecaster)):
    if forecaster is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ok", "model_loaded": True}

@app.get("/")
def read_root():
    return {"status": "ok", "message": "SOC API is running."}
