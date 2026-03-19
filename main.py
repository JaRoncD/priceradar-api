from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title="PriceRadar API", version="1.0.0")

@app.get("/")
async def root():
    return {
        "status": "ok",
        "project": "PriceRadar API",
        "version": "1.0.0"
    }