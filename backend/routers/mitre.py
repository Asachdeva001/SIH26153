import logging
from fastapi import APIRouter, HTTPException
from backend.src.world_model import RuleBasedMITREMapper
from backend.schemas.requests import MitreRequest, MitreResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/mitre", response_model=MitreResponse)
def get_mitre_stage(req: MitreRequest):
    try:
        custom_thresholds = req.custom_thresholds.model_dump()
        
        mitre_info = RuleBasedMITREMapper.map_state_to_stage(
            req.state_dict, 
            custom_thresholds=custom_thresholds
        )
        
        return mitre_info
    except (KeyError, ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=f"MITRE mapping failed — invalid state data: {e}")
    except Exception as e:
        logger.exception("MITRE mapping failed")
        raise HTTPException(status_code=500, detail=f"MITRE mapping failed: {e}")
