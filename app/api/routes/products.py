"""
routes/products.py
------------------
Endpoints para gestionar los productos (criptomonedas) que el usuario
quiere monitorear. Requieren autenticación JWT en todos los endpoints.

Endpoints:
    GET  /products          - Lista los productos del usuario
    POST /products          - Agrega un producto a monitorear
    GET  /products/{id}/history - Historial de precios de un producto
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import Product, UserProduct, PriceHistory, User
from app.schemas.product import ProductAdd, ProductOut, PriceHistoryOut
from app.api.dependencies import get_current_user
import httpx
from app.core.config import settings

router = APIRouter(prefix="/products", tags=["Productos"])


async def fetch_coin_data(coin_id: str) -> dict:
    """
    Consulta la API de CoinGecko para obtener información de una criptomoneda.
    
    Args:
        coin_id: identificador de CoinGecko (ej: 'bitcoin')
    
    Returns:
        Diccionario con name, symbol y precio actual en USD
    
    Raises:
        HTTPException 404 si el coin_id no existe en CoinGecko
    """
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
    Retorna la lista de criptomonedas que el usuario está monitoreando.
    Solo muestra los productos asociados al usuario autenticado.
    """
    result = await db.execute(
        select(Product)
        .join(UserProduct)
        .where(UserProduct.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/", response_model=ProductOut, status_code=201)
async def add_product(
    data: ProductAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Agrega una criptomoneda a la lista de monitoreo del usuario.
    
    Si el producto no existe en la base de datos, lo consulta en
    CoinGecko y lo crea. Luego asocia el producto al usuario actual.
    
    Raises:
        HTTPException 400 si el usuario ya está monitoreando ese producto
        HTTPException 404 si el coin_id no existe en CoinGecko
    """
    # Verificar si el producto ya existe en la DB
    result = await db.execute(
        select(Product).where(Product.coin_id == data.coin_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        # No existe, consultarlo en CoinGecko y crearlo
        coin_data = await fetch_coin_data(data.coin_id)
        product = Product(
            coin_id=data.coin_id,
            name=coin_data["name"],
            symbol=coin_data["symbol"].upper(),
            current_price=coin_data["market_data"]["current_price"].get("usd"),
        )
        db.add(product)
        await db.flush()  # obtiene el ID sin hacer commit aún

    # Verificar si el usuario ya lo está monitoreando
    existing = await db.execute(
        select(UserProduct).where(
            UserProduct.user_id == current_user.id,
            UserProduct.product_id == product.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Ya estás monitoreando este producto"
        )

    db.add(UserProduct(user_id=current_user.id, product_id=product.id))
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/{product_id}/history", response_model=List[PriceHistoryOut])
async def price_history(
    product_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna el historial de precios de un producto específico.
    
    Args:
        product_id: ID del producto en la base de datos
        limit: cantidad máxima de registros a retornar (default: 100)
    
    Returns:
        Lista de precios ordenados del más reciente al más antiguo
    """
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.recorded_at.desc())
        .limit(limit)
    )
    return result.scalars().all()