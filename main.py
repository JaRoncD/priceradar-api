"""
main.py
-------
Punto de entrada de la aplicación PriceRadar API.
"""

from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import auth, products

app = FastAPI(title="PriceRadar API", version="1.0.0")

app.include_router(auth.router)
app.include_router(products.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "project": "PriceRadar API"}