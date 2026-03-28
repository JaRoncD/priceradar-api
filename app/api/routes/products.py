"""
routes/products.py
------------------
Endpoints para gestionar productos (criptomonedas).

Endpoints públicos (cualquier usuario autenticado):
    GET  /products                  - Lista productos del usuario
    GET  /products/{id}/history     - Historial de precios

Endpoints privados (solo admin):
    POST   /products                - Agregar producto al sistema
    PUT    /products/{id}           - Editar nombre o símbolo
    DELETE /products/{id}           - Eliminar producto del sistema
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import Product, UserProduct, PriceHistory, User
from app.schemas.product import ProductAdd, ProductOut, PriceHistoryOut
from app.api.dependencies import get_current_user, get_admin_user
import httpx
from app.core.config import settings

router = APIRouter(prefix="/products", tags=["Productos"])


class ProductUpdate(BaseModel):
    """Campos que el admin puede modificar de un producto."""
    name: Optional[str] = None
    symbol: Optional[str] = None


async def fetch_coin_data(coin_id: str) -> dict:
    """Consulta CoinGecko y retorna los datos de una criptomoneda."""
    url = f"{settings.COINGECKO_URL}/coins/{coin_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        if response.status_code != 200:
            raise HTTPException(
                status_code=404,
                detail=f"Coin '{coin_id}' no encontrado en CoinGecko"
            )
        return response.json()


@router.get("/", response_model=List[ProductOut])
async def list_products(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna todos los productos registrados en el sistema.
    Accesible para cualquier usuario autenticado.
    """
    result = await db.execute(select(Product))
    return result.scalars().all()


@router.post("/", response_model=ProductOut, status_code=201)
async def add_product(
    data: ProductAdd,
    current_user: User = Depends(get_admin_user),  # ← solo admin
    db: AsyncSession = Depends(get_db),
):
    """
    Agrega una criptomoneda al sistema para que todos los usuarios
    puedan monitorearlo. Solo accesible para administradores.

    Raises:
        HTTPException 400 si el producto ya existe
        HTTPException 403 si el usuario no es admin
        HTTPException 404 si el coin_id no existe en CoinGecko
    """
    result = await db.execute(
        select(Product).where(Product.coin_id == data.coin_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El producto ya existe")

    coin_data = await fetch_coin_data(data.coin_id)
    product = Product(
        coin_id=data.coin_id,
        name=coin_data["name"],
        symbol=coin_data["symbol"].upper(),
        current_price=coin_data["market_data"]["current_price"].get("usd"),
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(get_admin_user),  # ← solo admin
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza el nombre o símbolo de un producto existente.
    Solo accesible para administradores.

    Raises:
        HTTPException 403 si el usuario no es admin
        HTTPException 404 si el producto no existe
    """
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Solo actualiza los campos que fueron enviados
    if data.name is not None:
        product.name = data.name
    if data.symbol is not None:
        product.symbol = data.symbol.upper()

    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_admin_user),  # ← solo admin
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina un producto del sistema junto con su historial de precios
    y las alertas asociadas. Solo accesible para administradores.

    Raises:
        HTTPException 403 si el usuario no es admin
        HTTPException 404 si el producto no existe
    """
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    await db.delete(product)
    await db.commit()


@router.get("/{product_id}/history", response_model=List[PriceHistoryOut])
async def price_history(
    product_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna el historial de precios de un producto específico.
    Accesible para cualquier usuario autenticado.
    """
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.recorded_at.desc())
        .limit(limit)
    )
    return result.scalars().all()