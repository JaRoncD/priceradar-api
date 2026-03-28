"""
routes/ws.py
------------
Endpoint WebSocket que transmite precios en tiempo real a los clientes conectados.
Cada 10 segundos consulta los precios actuales de la base de datos
y los envía a todos los clientes conectados simultáneamente.

Uso desde el cliente:
    const ws = new WebSocket("ws://localhost:8000/ws/prices");
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
    };
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Product

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Gestiona todas las conexiones WebSocket activas.
    Permite conectar, desconectar y enviar mensajes a todos
    los clientes conectados simultáneamente (broadcast).
    """

    def __init__(self):
        # Lista de conexiones WebSocket activas
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Acepta una nueva conexión y la registra."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Cliente conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Elimina una conexión de la lista de activas."""
        self.active_connections.remove(websocket)
        print(f"[WS] Cliente desconectado. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Envía un mensaje a todos los clientes conectados.
        Si un cliente falla, se desconecta automáticamente.
        """
        data = json.dumps(message)
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(data)
            except Exception:
                self.active_connections.remove(connection)


# Instancia global del manager — se comparte entre todas las conexiones
manager = ConnectionManager()


async def get_current_prices() -> list:
    """
    Consulta la base de datos y retorna los precios actuales
    de todos los productos registrados.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product))
        products = result.scalars().all()
        return [
            {
                "coin_id": p.coin_id,
                "name": p.name,
                "symbol": p.symbol,
                "price": p.current_price,
                "last_updated": p.last_updated.isoformat() if p.last_updated else None,
            }
            for p in products
        ]


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """
    Endpoint WebSocket que transmite precios cada 10 segundos.

    Flujo:
        1. Cliente se conecta a ws://localhost:8000/ws/prices
        2. El servidor envía los precios actuales inmediatamente
        3. Cada 10 segundos envía una actualización
        4. Si el cliente se desconecta, se limpia la conexión
    
    Formato del mensaje:
        {
            "type": "prices",
            "data": [
                {
                    "coin_id": "bitcoin",
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "price": 65000.0,
                    "last_updated": "2024-01-01T00:00:00"
                }
            ]
        }
    """
    await manager.connect(websocket)
    try:
        while True:
            # Obtener precios actuales de la DB
            prices = await get_current_prices()

            # Enviar a este cliente
            await websocket.send_text(json.dumps({
                "type": "prices",
                "data": prices
            }))

            # Esperar 10 segundos antes de la siguiente actualización
            await asyncio.sleep(10)

    except WebSocketDisconnect:
        manager.disconnect(websocket)