"""
main.py
-------
Punto de entrada de la aplicación PriceRadar API.
Configura el ciclo de vida de la app e inicia el scheduler
de tareas en background al arrancar.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api.routes import auth, products, alerts, ws
from app.services.price_fetcher import fetch_and_update_prices
from app.services.alert_engine import evaluate_alerts
from app.core.config import settings

# Instancia global del scheduler
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Controla el ciclo de vida de la aplicación.

    Al iniciar:
        - Arranca el scheduler con las tareas periódicas

    Al apagar:
        - Detiene el scheduler limpiamente
    """
    # Tarea 1: actualizar precios desde CoinGecko
    scheduler.add_job(
        fetch_and_update_prices,
        "interval",
        seconds=settings.PRICE_FETCH_INTERVAL,
        id="price_fetcher"
    )

    # Tarea 2: evaluar alertas después de cada actualización
    scheduler.add_job(
        evaluate_alerts,
        "interval",
        seconds=settings.PRICE_FETCH_INTERVAL,
        id="alert_engine"
    )

    scheduler.start()
    print(f"[PriceRadar] Scheduler iniciado. Actualizando cada {settings.PRICE_FETCH_INTERVAL}s.")

    yield  # la app corre aquí

    scheduler.shutdown()
    print("[PriceRadar] Scheduler detenido.")


app = FastAPI(
    title="PriceRadar API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(alerts.router)
app.include_router(ws.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "project": "PriceRadar API"}