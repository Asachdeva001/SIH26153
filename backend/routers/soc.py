from fastapi import APIRouter
from backend.src.world_model import SOCRiskPrioritizer
from backend.schemas.requests import SOCRequest, SOCResponse

router = APIRouter()

@router.post("/soc", response_model=SOCResponse)
def get_soc_priority(req: SOCRequest):
    mitre_stage = req.mitre_stage.dict()
    
    soc_priority = SOCRiskPrioritizer.calculate_prioritized_risk(
        req.forecast_risk, 
        req.asset_ip, 
        mitre_stage
    )
    
    return soc_priority
