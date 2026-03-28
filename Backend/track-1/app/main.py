from fastapi import FastAPI

from app.routers.generate_data import router as generate_data_router

app = FastAPI(title="Track-1 API")
app.include_router(generate_data_router, prefix="/api", tags=["generate_data"])


@app.get("/health")
def health():
    return {"ok": True}
