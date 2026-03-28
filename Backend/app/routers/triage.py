from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.triage import predict_triage

router = APIRouter()


class TriagePredictionRequest(BaseModel):
    query: str = Field(
        ..., min_length=5, description="Natural language patient summary."
    )
    labs: dict[str, float] | None = Field(
        default=None,
        description="Optional structured lab values keyed by dataset lab name.",
    )
    medications: list[str] | None = Field(
        default=None,
        description="Optional structured medication names to supplement query parsing.",
    )


class TriagePredictionResponse(BaseModel):
    chief_complaint: str
    chief_complaint_confidence: float
    predicted_triage_level: int
    chief_complaint_baseline_triage: int
    extracted_labs: dict[str, float]
    extracted_medications: list[str]
    probabilities: list[dict[str, Any]]
    supported_labs: list[str]
    supported_medications: list[str]


@router.post("/triage/predict", response_model=TriagePredictionResponse)
def triage_predict(req: TriagePredictionRequest):
    result = predict_triage(
        query=req.query,
        labs=req.labs,
        medications=req.medications,
    )
    return TriagePredictionResponse(**result)
