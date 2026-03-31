from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api.routes import auth, products, alerts, ws
from app.services.price_fetcher import fetch_and_update_prices
from app.services.alert_engine import evaluate_alerts
from app.core.config import settings

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(fetch_and_update_prices, "interval", seconds=settings.PRICE_FETCH_INTERVAL, id="price_fetcher")
    scheduler.add_job(evaluate_alerts, "interval", seconds=settings.PRICE_FETCH_INTERVAL, id="alert_engine")
    scheduler.start()
    print(f"[PriceRadar] Scheduler iniciado. Actualizando cada {settings.PRICE_FETCH_INTERVAL}s.")
    yield
    scheduler.shutdown()

app = FastAPI(title="PriceRadar API", version="1.0.0", lifespan=lifespan)

# ── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # origen del frontend Angular
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(alerts.router)
app.include_router(ws.router)

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "project": "PriceRadar API"}