"""
routes/alerts.py
----------------
Endpoints para gestionar alertas de precio.
Una alerta notifica al usuario cuando una criptomoneda
supera o baja de un precio objetivo.

Endpoints:
    POST   /alerts       - Crear una alerta de precio
    GET    /alerts/me    - Ver todas las alertas del usuario
    DELETE /alerts/{id}  - Eliminar una alerta
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import Alert, Product, User
from app.schemas.product import AlertCreate, AlertOut
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alertas"])


@router.post("/", response_model=AlertOut, status_code=201)
async def create_alert(
    data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea una alerta de precio para un producto específico.

    El campo condition acepta dos valores:
        - 'above': se dispara cuando el precio sube por encima de target_price
        - 'below': se dispara cuando el precio baja por debajo de target_price

    Raises:
        HTTPException 400 si condition no es 'above' o 'below'
        HTTPException 404 si el producto no existe
    """
    if data.condition not in ("above", "below"):
        raise HTTPException(
            status_code=400,
            detail="condition debe ser 'above' o 'below'"
        )

    # Verificar que el producto existe en la DB
    result = await db.execute(
        select(Product).where(Product.id == data.product_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    alert = Alert(
        user_id=current_user.id,
        product_id=data.product_id,
        target_price=data.target_price,
        condition=data.condition,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.get("/me", response_model=List[AlertOut])
async def my_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna todas las alertas del usuario autenticado.
    Incluye tanto las alertas activas como las ya disparadas.
    """
    result = await db.execute(
        select(Alert).where(Alert.user_id == current_user.id)
    )
    return result.scalars().all()


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina una alerta del usuario autenticado.
    Solo puede eliminar sus propias alertas.

    Raises:
        HTTPException 404 si la alerta no existe o no pertenece al usuario
    """
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    await db.delete(alert)
    await db.commit()