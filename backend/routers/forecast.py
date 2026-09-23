import pandas as pd
from fastapi import APIRouter, Depends
from backend.models.loader import get_forecaster
from backend.schemas.requests import ForecastRequest, ForecastResponse

router = APIRouter()

@router.post("/forecast", response_model=ForecastResponse)
def get_forecast(req: ForecastRequest, forecaster=Depends(get_forecaster)):
    if not req.windows:
        return {"forecast_df": [], "risk_trajectory": []}
        
    df_win = pd.DataFrame(req.windows)
    
    # Run K-step Forecast Simulation
    forecast_results = forecaster.predict_k_steps(df_win, K=req.K)
    df_forecast = forecast_results['forecast_df']
    risk_trajectory = forecast_results['risk_trajectory']
    
    forecast_dict = df_forecast.to_dict(orient='records')
    
    return {
        "forecast_df": forecast_dict,
        "risk_trajectory": risk_trajectory
    }
