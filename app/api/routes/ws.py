"""
routes/ws.py
------------
Endpoint WebSocket con autenticación JWT.
El cliente debe enviar el token como primer mensaje antes de
recibir cualquier dato. Si el token es inválido se cierra la conexión.
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Product, User
from app.core.security import decode_token

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Gestiona todas las conexiones WebSocket activas.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Acepta una nueva conexión y la registra."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Cliente conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Elimina una conexión de la lista de activas."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[WS] Cliente desconectado. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Envía un mensaje a todos los clientes conectados."""
        data = json.dumps(message)
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(data)
            except Exception:
                self.active_connections.remove(connection)


manager = ConnectionManager()


async def get_current_prices() -> list:
    """Consulta los precios actuales de todos los productos en la DB."""
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


async def authenticate_websocket(websocket: WebSocket) -> bool:
    """
    Espera el token JWT como primer mensaje del cliente.
    Retorna True si el token es válido, False si no lo es.

    Flujo:
        1. Cliente se conecta
        2. Servidor espera el token (máximo 10 segundos)
        3. Si el token es válido, empieza la transmisión
        4. Si no, cierra la conexión con código 4001
    """
    try:
        # Esperar el token con timeout de 10 segundos
        token_message = await asyncio.wait_for(
            websocket.receive_text(),
            timeout=10.0
        )
        payload = decode_token(token_message)
        if not payload:
            await websocket.close(code=4001, reason="Token inválido")
            return False
        return True
    except asyncio.TimeoutError:
        await websocket.close(code=4001, reason="Tiempo de autenticación agotado")
        return False


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """
    Endpoint WebSocket autenticado que transmite precios cada 10 segundos.

    Flujo:
        1. Cliente se conecta a ws://localhost:8000/ws/prices
        2. Cliente envía el JWT como primer mensaje
        3. Si es válido, el servidor empieza a transmitir precios
        4. Cada 10 segundos llega una actualización

    Formato del mensaje recibido:
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

    # Validar token antes de transmitir
    authenticated = await authenticate_websocket(websocket)
    if not authenticated:
        manager.disconnect(websocket)
        return

    await websocket.send_text(json.dumps({"type": "auth", "status": "ok"}))

    try:
        while True:
            prices = await get_current_prices()
            await websocket.send_text(json.dumps({
                "type": "prices",
                "data": prices
            }))
            await asyncio.sleep(10)

    except WebSocketDisconnect:
        manager.disconnect(websocket)