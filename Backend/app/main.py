from fastapi import FastAPI

from app.routers.generate_data import router as generate_data_router
from app.routers.triage import router as triage_router

app = FastAPI(title="Backend API")
app.include_router(generate_data_router, prefix="/api", tags=["generate_data"])
app.include_router(triage_router, prefix="/api", tags=["triage"])


@app.get("/health")
def health():
    return {"ok": True}
