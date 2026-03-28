"""
schemas/product.py
------------------
Esquemas Pydantic para validar datos de entrada y salida
relacionados con productos (criptomonedas) y alertas.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ProductAdd(BaseModel):
    """
    Datos requeridos para agregar un producto a monitorear.
    El coin_id debe corresponder al identificador de CoinGecko.
    
    Ejemplos de coin_id válidos: 'bitcoin', 'ethereum', 'solana'
    """
    coin_id: str


class ProductOut(BaseModel):
    """
    Datos del producto que retorna la API.
    Incluye el precio actual y la última vez que fue actualizado.
    """
    id: int
    coin_id: str
    name: str
    symbol: str
    current_price: Optional[float]
    last_updated: Optional[datetime]

    model_config = {"from_attributes": True}


class AlertCreate(BaseModel):
    """
    Datos requeridos para crear una alerta de precio.
    
    condition puede ser:
        - 'above': notificar cuando el precio suba de target_price
        - 'below': notificar cuando el precio baje de target_price
    """
    product_id: int
    target_price: float
    condition: str


class AlertOut(BaseModel):
    """Datos de la alerta que retorna la API."""
    id: int
    product_id: int
    target_price: float
    condition: str
    is_active: bool
    triggered_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class PriceHistoryOut(BaseModel):
    """Representa un registro del historial de precios."""
    price: float
    recorded_at: datetime

    model_config = {"from_attributes": True}