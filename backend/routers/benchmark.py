import logging
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from backend.models.loader import get_baseline
from backend.src.world_model import BenchmarkEvaluator
from backend.schemas.requests import BenchmarkRequest, BenchmarkResponse

router = APIRouter()
logger = logging.getLogger(__name__)

EMPTY_BENCHMARK = {
    "world_model": {"f1": 0.0, "precision": 0.0, "recall": 0.0, "fpr": 0.0, "lead_time_windows": 0.0},
    "baseline": {"f1": 0.0, "precision": 0.0, "recall": 0.0, "fpr": 0.0, "lead_time_windows": 0.0},
    "gain_f1_pct": 0.0,
    "lead_time_advantage": 0.0
}

@router.post("/benchmark", response_model=BenchmarkResponse)
def get_benchmark(req: BenchmarkRequest, baseline=Depends(get_baseline)):
    if baseline is None:
        raise HTTPException(status_code=503, detail="Baseline model not loaded. Server is still initializing.")

    if not req.windows or len(req.windows) < req.K:
        return EMPTY_BENCHMARK
    
    try:
        df_win = pd.DataFrame(req.windows)
        
        wm_preds = np.array(req.risk_trajectory)
        
        # Baseline predictions for the same future window (static)
        base_preds = baseline.predict_proba(df_win)[-req.K:]
        
        if 'is_attack' in df_win.columns:
            gt_binary = df_win['is_attack'].values[-req.K:]
        elif 'target_risk_score' in df_win.columns:
            gt_binary = (df_win['target_risk_score'].values[-req.K:] > 0.30).astype(int)
        else:
            gt_binary = np.zeros(req.K, dtype=int)
        
        bench_res = BenchmarkEvaluator.evaluate_comparison(
            wm_preds, 
            base_preds, 
            gt_binary, 
            threshold=req.threshold
        )
        
        return bench_res
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Benchmark evaluation failed — invalid input: {e}")
    except Exception as e:
        logger.exception("Benchmark evaluation failed")
        raise HTTPException(status_code=500, detail=f"Benchmark evaluation failed: {e}")
