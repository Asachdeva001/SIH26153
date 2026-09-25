import os
from backend.src.world_model import WorldModelForecaster, BaselineClassifier
from backend.src.synthetic_generator import SyntheticAttackGenerator

class MLModelLoader:
    def __init__(self):
        self.forecaster = None
        self.baseline = None

    def load_models(self):
        # Load World Model
        if os.path.exists("models/world_model_v1.pth"):
            self.forecaster = WorldModelForecaster.load_model("models/world_model_v1.pth")
            if os.path.exists("models/scaler.pkl"):
                import joblib
                scaler_data = joblib.load("models/scaler.pkl")
                self.forecaster.mean_ = scaler_data['mean_']
                self.forecaster.scale_ = scaler_data['scale_']
        else:
            # Stopgap: live fit
            gen = SyntheticAttackGenerator(seed=42)
            _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=20)
            self.forecaster = WorldModelForecaster(history_len=4)
            self.forecaster.fit(df_win)

        # Load Baseline
        if os.path.exists("models/baseline_lr_v1.pkl"):
            import joblib
            self.baseline = joblib.load("models/baseline_lr_v1.pkl")
        else:
            gen = SyntheticAttackGenerator(seed=42)
            _, df_win = gen.generate_scenario("APT Multi-Stage Campaign", num_windows=20)
            self.baseline = BaselineClassifier()
            self.baseline.fit(df_win)

# Singleton instance
ml_models = MLModelLoader()

def get_forecaster():
    return ml_models.forecaster

def get_baseline():
    return ml_models.baseline
