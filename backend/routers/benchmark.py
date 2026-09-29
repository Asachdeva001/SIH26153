import logging
import os
import numpy as np
from fastapi import APIRouter, HTTPException
from backend.schemas.requests import BenchmarkRequest, BenchmarkResponse
from backend.src.world_model import BenchmarkEvaluator

router = APIRouter()
logger = logging.getLogger(__name__)

EMPTY_BENCHMARK = {
    "world_model": {"f1": 0.0, "precision": 0.0, "recall": 0.0, "fpr": 0.0, "lead_time_windows": 0.0},
    "baseline": {"f1": 0.0, "precision": 0.0, "recall": 0.0, "fpr": 0.0, "lead_time_windows": 0.0},
    "gain_f1_pct": 0.0,
    "lead_time_advantage": 0.0
}

@router.post("/benchmark", response_model=BenchmarkResponse)
def get_benchmark(req: BenchmarkRequest):
    if not req.windows or len(req.windows) < 2 or len(req.risk_trajectory) == 0:
        return EMPTY_BENCHMARK

    try:
        gt = []
        for window in req.windows:
            if "is_attack" in window:
                gt.append(int(bool(window["is_attack"])))
            elif "target_risk_score" in window:
                gt.append(int(float(window["target_risk_score"]) > 0.30))
            else:
                gt.append(0)

        wm_probs = np.asarray(req.risk_trajectory[: len(req.windows)], dtype=float)
        if wm_probs.size == 0:
            return EMPTY_BENCHMARK

        baseline_probs = np.asarray([
            float(window.get("target_risk_score", 0.0)) for window in req.windows[: len(wm_probs)]
        ], dtype=float)

        if len(gt) < 2 or len(wm_probs) < 2 or len(baseline_probs) < 2:
            return EMPTY_BENCHMARK

        metrics = BenchmarkEvaluator.evaluate_comparison(
            world_model_preds=wm_probs,
            baseline_preds=baseline_probs,
            ground_truth=np.asarray(gt[: len(wm_probs)], dtype=int),
            threshold=req.threshold,
        )
        return metrics
    except Exception as e:
        logger.exception("Failed to evaluate benchmark comparison")
        raise HTTPException(status_code=500, detail=f"Benchmark evaluation failed: {e}")
