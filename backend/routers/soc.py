import logging
from fastapi import APIRouter, HTTPException
from backend.src.world_model import SOCRiskPrioritizer
from backend.schemas.requests import SOCRequest, SOCResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/soc", response_model=SOCResponse)
def get_soc_priority(req: SOCRequest):
    try:
        mitre_stage = req.mitre_stage.model_dump()
        
        soc_priority = SOCRiskPrioritizer.calculate_prioritized_risk(
            req.forecast_risk, 
            req.asset_ip, 
            mitre_stage
        )
        
        return soc_priority
    except (KeyError, ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=f"SOC prioritization failed — invalid input: {e}")
    except Exception as e:
        logger.exception("SOC prioritization failed")
        raise HTTPException(status_code=500, detail=f"SOC prioritization failed: {e}")
