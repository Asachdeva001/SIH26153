import time
from fastapi import APIRouter
from backend.schemas.requests import ReportRequest

router = APIRouter()

@router.post("/report")
def generate_report(req: ReportRequest):
    # Simply format and return the data as the authoritative JSON report
    report_data = {
        "organization": "National Cyber Defense Operations",
        "classification": "OFFICIAL USE ONLY",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "target_asset": req.target_asset,
        "soc_risk_prioritization": req.soc_risk_prioritization,
        "scenario": req.scenario,
        "current_window_id": req.current_window_id,
        "current_risk_score": req.current_risk_score,
        "projected_peak_risk_score": req.projected_peak_risk_score,
        "mitre_current_phase": req.mitre_current_phase,
        "mitre_predicted_phase": req.mitre_predicted_phase,
        "forecast_horizon_k": req.forecast_horizon_k,
        "primary_driver": req.primary_driver,
        "narrative": req.narrative,
        "recommended_playbook": [action.dict() for action in req.recommended_playbook]
    }
    
    return report_data
