import json
import logging
from fastapi import APIRouter, HTTPException
from backend.src.synthetic_generator import SyntheticAttackGenerator
from backend.schemas.requests import ScenarioResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/scenario", response_model=ScenarioResponse)
def get_scenario(name: str = "APT Multi-Stage Campaign", num_windows: int = 20, window_size_sec: float = 10.0):
    try:
        gen = SyntheticAttackGenerator(seed=42)
        df_raw, df_win = gen.generate_scenario(name, num_windows=num_windows, window_size_sec=window_size_sec)
        
        # Convert DataFrames to dict lists
        # Replace NaNs with None for JSON serialization
        df_win_clean = df_win.replace({float('nan'): None})
        windows = df_win_clean.to_dict(orient='records')
        
        # We only return the top 50 raw packets to save bandwidth for topology
        df_raw_sub = df_raw.head(50).replace({float('nan'): None})
        raw_packets = df_raw_sub.to_dict(orient='records')
        
        # ensure timestamp formatting
        for pkt in raw_packets:
            if 'timestamp' in pkt and pkt['timestamp'] is not None:
                pkt['timestamp'] = str(pkt['timestamp'])
                
        return {"windows": windows, "raw_packets": raw_packets}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid scenario parameters: {e}")
    except Exception as e:
        logger.exception("Scenario generation failed")
        raise HTTPException(status_code=500, detail=f"Scenario generation failed: {e}")
