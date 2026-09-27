import logging
import pandas as pd
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from backend.models.loader import get_forecaster
from backend.schemas.requests import ForecastRequest, ForecastResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/forecast", response_model=ForecastResponse)
async def get_forecast(req: ForecastRequest, forecaster=Depends(get_forecaster)):
    if forecaster is None:
        raise HTTPException(status_code=503, detail="World model not loaded. Server is still initializing.")

    if not req.windows:
        return {"forecast_df": [], "risk_trajectory": []}
    
    try:
        df_win = pd.DataFrame(req.windows)
        
        # Run K-step Forecast Simulation in a background thread to prevent blocking event loop
        forecast_results = await asyncio.to_thread(forecaster.predict_k_steps, df_win, K=req.K)
        df_forecast = forecast_results['forecast_df']
        risk_trajectory = forecast_results['risk_trajectory']
        
        forecast_dict = df_forecast.to_dict(orient='records')
        
        return {
            "forecast_df": forecast_dict,
            "risk_trajectory": risk_trajectory
        }
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Forecast failed — invalid window data: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Forecast model error: {e}")
    except Exception as e:
        logger.exception("Forecast failed")
        raise HTTPException(status_code=500, detail=f"Forecast failed: {e}")
