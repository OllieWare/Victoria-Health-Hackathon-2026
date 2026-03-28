from pathlib import Path

import joblib

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = BACKEND_ROOT / "models" / "fraud_model.joblib"


def load_sklearn_model():
    model = joblib.load(MODEL_PATH)
    return model
