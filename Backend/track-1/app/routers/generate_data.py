from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.synthetic import make_synthetic_rows

router = APIRouter()


class GenerateDataRequest(BaseModel):
    n_rows: int = Field(default=5, ge=1, le=1000)
    seed: int | None = 42


class GenerateDataResponse(BaseModel):
    rows: list[dict]
    count: int


@router.post("/generate_data", response_model=GenerateDataResponse)
def generate_data(req: GenerateDataRequest):
    rows = make_synthetic_rows(n_rows=req.n_rows, seed=req.seed)
    return GenerateDataResponse(rows=rows, count=len(rows))