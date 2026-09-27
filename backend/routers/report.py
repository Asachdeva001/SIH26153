import time
import logging
from fastapi import APIRouter, HTTPException
from backend.schemas.requests import ReportRequest

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/report")
def generate_report(req: ReportRequest):
    try:
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
            "recommended_playbook": [action.model_dump() for action in req.recommended_playbook]
        }
        
        return report_data
    except (KeyError, ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=f"Report generation failed — invalid input: {e}")
    except Exception as e:
        logger.exception("Report generation failed")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")
