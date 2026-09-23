from fastapi import APIRouter
from src.world_model import RuleBasedMITREMapper
from backend.schemas.requests import MitreRequest, MitreResponse

router = APIRouter()

@router.post("/mitre", response_model=MitreResponse)
def get_mitre_stage(req: MitreRequest):
    # Convert Pydantic object to dict
    custom_thresholds = req.custom_thresholds.dict()
    
    mitre_info = RuleBasedMITREMapper.map_state_to_stage(
        req.state_dict, 
        custom_thresholds=custom_thresholds
    )
    
    return mitre_info
