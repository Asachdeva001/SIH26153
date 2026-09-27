import logging
import pandas as pd
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from backend.models.loader import get_explainer
from backend.src.world_model import AssetCriticalityManager
from backend.schemas.requests import XAIRequest, XAIResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/xai", response_model=XAIResponse)
async def get_xai_attribution(req: XAIRequest, explainer=Depends(get_explainer)):
    if explainer is None:
        raise HTTPException(status_code=503, detail="XAI explainer not loaded. Server is still initializing.")

    if not req.windows:
        return {"attributions": [], "primary_driver": "None", "narrative": "No data"}
    
    try:
        df_win_sub = pd.DataFrame(req.windows)
        asset_info = AssetCriticalityManager.get_asset_info(req.asset_ip)
        
        # Run Explainer in a background thread to prevent blocking event loop
        xai_res = await asyncio.to_thread(explainer.explain_window, df_win_sub, asset_info=asset_info, soc_priority=None)
        
        return {
            "attributions": xai_res['attributions'],
            "primary_driver": xai_res['primary_driver'],
            "narrative": xai_res['narrative']
        }
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"XAI attribution failed — invalid window data: {e}")
    except Exception as e:
        logger.exception("XAI attribution failed")
        raise HTTPException(status_code=500, detail=f"XAI attribution failed: {e}")
