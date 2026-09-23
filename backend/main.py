import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.loader import ml_models
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

app = FastAPI(
    title="Predictive Cyber Defense & SOC API",
    description="Backend API for AI-driven attack forecasting and SOC playbooks.",
    version="1.0.0"
)

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Ensure scratch and models directories exist
    os.makedirs("scratch", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    # Load ML models on startup
    ml_models.load_models()

# Mount routers
app.include_router(scenario.router, prefix="/api", tags=["scenario"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(forecast.router, prefix="/api", tags=["forecast"])
app.include_router(mitre.router, prefix="/api", tags=["mitre"])
app.include_router(xai.router, prefix="/api", tags=["xai"])
app.include_router(soc.router, prefix="/api", tags=["soc"])
app.include_router(benchmark.router, prefix="/api", tags=["benchmark"])
app.include_router(report.router, prefix="/api", tags=["report"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "SOC API is running."}
