from pathlib import Path

import joblib

MODEL_PATH = Path("track-1/models/fraud_model.joblib")


def load_sklearn_model():
    model = joblib.load(MODEL_PATH)
    return model