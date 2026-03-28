"""
price_fetcher.py
----------------
Servicio que consulta CoinGecko periódicamente y actualiza
los precios de todos los productos registrados en la base de datos.

Se ejecuta como tarea en background cada N segundos según
PRICE_FETCH_INTERVAL definido en el .env
"""

from datetime import datetime
import httpx
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Product, PriceHistory
from app.core.config import settings


async def fetch_and_update_prices():
    """
    Tarea principal del background job.

    Flujo:
        1. Obtiene todos los productos registrados en la DB
        2. Consulta sus precios actuales en CoinGecko en una sola llamada
        3. Actualiza el precio actual de cada producto
        4. Guarda un registro en price_history por cada producto
    
    Si CoinGecko falla, imprime el error y espera al siguiente ciclo
    sin romper la aplicación.
    """
    async with AsyncSessionLocal() as db:
        # Obtener todos los productos registrados
        result = await db.execute(select(Product))
        products = result.scalars().all()

        if not products:
            print("[PriceFetcher] No hay productos registrados, saltando...")
            return

        # Construir lista de coin_ids para consultar en una sola llamada
        # Ejemplo: "bitcoin,ethereum,solana"
        coin_ids = ",".join(p.coin_id for p in products)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.COINGECKO_URL}/simple/price",
                    params={"ids": coin_ids, "vs_currencies": "usd"},
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            print(f"[PriceFetcher] Error consultando CoinGecko: {e}")
            return

        # Actualizar precio de cada producto y guardar en historial
        now = datetime.utcnow()
        updated = 0
        for product in products:
            price = data.get(product.coin_id, {}).get("usd")
            if price is not None:
                product.current_price = price
                product.last_updated = now
                db.add(PriceHistory(product_id=product.id, price=price))
                updated += 1

        await db.commit()
        print(f"[PriceFetcher] {updated} precios actualizados a las {now.strftime('%H:%M:%S')}")