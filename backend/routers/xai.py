import pandas as pd
from fastapi import APIRouter, Depends
from backend.models.loader import get_forecaster
from backend.src.explainer import AttackExplainer
from backend.src.world_model import AssetCriticalityManager
from backend.schemas.requests import XAIRequest, XAIResponse

router = APIRouter()

@router.post("/xai", response_model=XAIResponse)
def get_xai_attribution(req: XAIRequest, forecaster=Depends(get_forecaster)):
    if not req.windows:
        return {"attributions": [], "primary_driver": "None", "narrative": "No data"}
        
    df_win_sub = pd.DataFrame(req.windows)
    asset_info = AssetCriticalityManager.get_asset_info(req.asset_ip)
    
    # In a real deployed app, background_df should be pre-cached
    # For now, we use the current window sequence as background to initialize Explainer
    explainer = AttackExplainer(
        model=forecaster.model,
        history_len=forecaster.history_len,
        mean=forecaster.mean_,
        scale=forecaster.scale_,
        device=forecaster.device,
        background_df=df_win_sub
    )
    
    xai_res = explainer.explain_window(df_win_sub, asset_info=asset_info, soc_priority=None)
    
    return {
        "attributions": xai_res['attributions'],
        "primary_driver": xai_res['primary_driver'],
        "narrative": xai_res['narrative']
    }
