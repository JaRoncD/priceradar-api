"""
main.py
-------
Punto de entrada de la aplicación PriceRadar API.
Registra los routers y configura el ciclo de vida de la app.
"""

from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import auth

app = FastAPI(title="PriceRadar API", version="1.0.0")

# Registrar routers
app.include_router(auth.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "project": "PriceRadar API"}