import os
import torch
from backend.src.world_model import WorldModelForecaster, BaselineClassifier
from backend.src.synthetic_generator import SyntheticAttackGenerator
from backend.src.explainer import AttackExplainer

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))

class MLModelLoader:
    def __init__(self):
        self.forecaster = None
        self.baseline = None
        self.explainer = None

    def _fallback_to_synthetic(self, label: str):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("%s; falling back to synthetic live-fit.", label)
        gen = SyntheticAttackGenerator(seed=42)
        _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=20)
        return df_win

    def load_models(self):
        import logging
        logger = logging.getLogger(__name__)
        allow_synthetic_fallback = os.getenv("ALLOW_SYNTHETIC_FALLBACK", "true").lower() == "true"
        
        # Load World Model
        try:
            world_model_path = os.path.join(MODELS_DIR, "world_model_v1.pth")
            scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
            if os.path.exists(world_model_path):
                state = torch.load(world_model_path, map_location="cpu", weights_only=False)
                if state.get("hidden_dim") != 64 or state.get("history_len") != 8:
                    mismatch_msg = (
                        "World model checkpoint contract mismatch: expected hidden_dim=64 "
                        f"and history_len=8, got hidden_dim={state.get('hidden_dim')}, "
                        f"history_len={state.get('history_len')}"
                    )
                    if not allow_synthetic_fallback:
                        raise ValueError(mismatch_msg)
                    logger.warning(mismatch_msg)
                    df_win = self._fallback_to_synthetic("Legacy or mismatched checkpoint detected")
                    self.forecaster = WorldModelForecaster(history_len=8)
                    self.forecaster.fit(df_win)
                else:
                    self.forecaster = WorldModelForecaster.load_model(world_model_path)
                    if os.path.exists(scaler_path):
                        import joblib
                        scaler_data = joblib.load(scaler_path)
                        self.forecaster.mean_ = scaler_data['mean_']
                        self.forecaster.scale_ = scaler_data['scale_']
            else:
                raise FileNotFoundError(f"World model artifact not found: {world_model_path}")
        except Exception as e:
            if not allow_synthetic_fallback:
                raise
            logger.error(f"Failed to load world model ({e}). Falling back to synthetic live-fit.")
            df_win = self._fallback_to_synthetic(str(e))
            self.forecaster = WorldModelForecaster(history_len=8)
            self.forecaster.fit(df_win)

        # Load Baseline
        try:
            baseline_path = os.path.join(MODELS_DIR, "baseline_lr_v1.pkl")
            if os.path.exists(baseline_path):
                import joblib
                self.baseline = joblib.load(baseline_path)
            else:
                raise FileNotFoundError(f"Baseline model artifact not found: {baseline_path}")
        except Exception as e:
            if not allow_synthetic_fallback:
                raise
            logger.error(f"Failed to load baseline model ({e}). Falling back to synthetic live-fit.")
            gen = SyntheticAttackGenerator(seed=42)
            _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=20)
            self.baseline = BaselineClassifier()
            self.baseline.fit(df_win)
            
        # Initialize Explainer with a generic benign baseline
        gen = SyntheticAttackGenerator(seed=42)
        _, bg_df = gen.generate_scenario("Benign Intranet Baseline", num_windows=50)
        self.explainer = AttackExplainer(
            model=self.forecaster.model,
            history_len=self.forecaster.history_len,
            mean=self.forecaster.mean_,
            scale=self.forecaster.scale_,
            device=self.forecaster.device,
            background_df=bg_df
        )

# Singleton instance
ml_models = MLModelLoader()

def get_forecaster():
    return ml_models.forecaster

def get_baseline():
    return ml_models.baseline

def get_explainer():
    return ml_models.explainer
