import os
from backend.src.world_model import WorldModelForecaster, BaselineClassifier
from backend.src.synthetic_generator import SyntheticAttackGenerator
from backend.src.explainer import AttackExplainer

class MLModelLoader:
    def __init__(self):
        self.forecaster = None
        self.baseline = None
        self.explainer = None

    def load_models(self):
        import logging
        logger = logging.getLogger(__name__)
        
        # Load World Model
        try:
            if os.path.exists("models/world_model_v1.pth"):
                self.forecaster = WorldModelForecaster.load_model("models/world_model_v1.pth")
                if os.path.exists("models/scaler.pkl"):
                    import joblib
                    scaler_data = joblib.load("models/scaler.pkl")
                    self.forecaster.mean_ = scaler_data['mean_']
                    self.forecaster.scale_ = scaler_data['scale_']
            else:
                raise FileNotFoundError("World model artifact not found.")
        except Exception as e:
            logger.warning(f"Failed to load world model ({e}). Falling back to synthetic live-fit.")
            gen = SyntheticAttackGenerator(seed=42)
            _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=20)
            self.forecaster = WorldModelForecaster(history_len=4)
            self.forecaster.fit(df_win)

        # Load Baseline
        try:
            if os.path.exists("models/baseline_lr_v1.pkl"):
                import joblib
                self.baseline = joblib.load("models/baseline_lr_v1.pkl")
            else:
                raise FileNotFoundError("Baseline model artifact not found.")
        except Exception as e:
            logger.warning(f"Failed to load baseline model ({e}). Falling back to synthetic live-fit.")
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
