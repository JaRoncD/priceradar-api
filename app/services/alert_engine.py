"""
alert_engine.py
---------------
Servicio que evalúa las alertas activas y las dispara
cuando el precio actual cumple la condición configurada.

Se ejecuta justo después de cada actualización de precios.
"""

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.db.models import Alert


async def evaluate_alerts():
    """
    Evalúa todas las alertas activas contra los precios actuales.

    Flujo:
        1. Obtiene todas las alertas activas con su producto asociado
        2. Evalúa si el precio actual cumple la condición de cada alerta
        3. Si se cumple, marca la alerta como disparada (is_active = False)
        4. Imprime un mensaje por cada alerta disparada

    Condiciones:
        - 'below': se dispara si current_price < target_price
        - 'above': se dispara si current_price > target_price
    """
    async with AsyncSessionLocal() as db:
        # Cargar alertas activas junto con su producto (evita N+1 queries)
        result = await db.execute(
            select(Alert)
            .where(Alert.is_active == True)
            .options(selectinload(Alert.product))
        )
        alerts = result.scalars().all()

        if not alerts:
            return

        triggered = 0
        for alert in alerts:
            product = alert.product

            # Saltar si el producto aún no tiene precio registrado
            if product.current_price is None:
                continue

            condition_met = (
                alert.condition == "below"
                and product.current_price < alert.target_price
            ) or (
                alert.condition == "above"
                and product.current_price > alert.target_price
            )

            if condition_met:
                alert.is_active = False
                alert.triggered_at = datetime.utcnow()
                triggered += 1
                print(
                    f"[AlertEngine] ¡Alerta disparada! {product.name} "
                    f"está en ${product.current_price:,.2f} "
                    f"(condición: {alert.condition} ${alert.target_price:,.2f})"
                )

        if triggered:
            await db.commit()
            print(f"[AlertEngine] {triggered} alerta(s) disparada(s).")