"""
models.py
---------
Define los modelos ORM del proyecto. Cada clase representa una tabla
en la base de datos PostgreSQL.

Tablas:
    - User: usuarios registrados en la app
    - Product: criptomonedas a monitorear (via CoinGecko)
    - PriceHistory: historial de precios registrados periodicamente
    - Alert: alertas de precio configuradas por cada usuario
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class User(Base):
    """
    Representa un usuario registrado en PriceRadar.

    Columnas:
        id: clave primaria autoincremental
        email: correo único, usado para login
        username: nombre de usuario único
        hashed_password: contraseña encriptada con bcrypt
        is_active: permite deshabilitar usuarios sin borrarlos
        created_at: fecha de registro, se asigna automáticamente
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relaciones
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user")
    products: Mapped[list["UserProduct"]] = relationship(back_populates="user")


class Product(Base):
    """
    Representa una criptomoneda registrada para monitoreo.

    El campo coin_id corresponde al identificador de CoinGecko
    (ej: 'bitcoin', 'ethereum', 'solana').

    Columnas:
        coin_id: identificador único de CoinGecko
        name: nombre completo (ej: Bitcoin)
        symbol: símbolo del mercado (ej: BTC)
        current_price: último precio registrado en USD
        last_updated: fecha de la última actualización de precio
    """
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    coin_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    symbol: Mapped[str] = mapped_column(String(20))
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relaciones: un producto tiene historial de precios y alertas asociadas
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="product")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="product")
    user_products: Mapped[list["UserProduct"]] = relationship(back_populates="product")


class PriceHistory(Base):
    """
    Registra cada precio capturado por el background job.

    Cada vez que el price_fetcher consulta CoinGecko, guarda
    una fila aquí por cada producto monitorado.

    Columnas:
        product_id: referencia al producto
        price: precio en USD en el momento de la captura
        recorded_at: timestamp de la captura, asignado automáticamente
    """
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    price: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="price_history")


class Alert(Base):
    """
    Alerta de precio configurada por un usuario sobre un producto.

    El alert_engine evalúa estas alertas periódicamente y las marca
    como disparadas cuando se cumple la condición.

    Columnas:
        user_id: usuario dueño de la alerta
        product_id: producto a vigilar
        target_price: precio objetivo en USD
        condition: 'above' (precio sube de X) o 'below' (precio baja de X)
        is_active: False cuando la alerta ya fue disparada
        triggered_at: fecha en que se cumplió la condición
        created_at: fecha de creación de la alerta
    """
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    target_price: Mapped[float] = mapped_column(Float)
    condition: Mapped[str] = mapped_column(String(10))  # "above" o "below"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="alerts")
    product: Mapped["Product"] = relationship(back_populates="alerts")

class UserProduct(Base):
    """
    Tabla intermedia que relaciona usuarios con productos.
    Permite que cada usuario tenga su propia lista de criptomonedas a monitorear.

    Columnas:
        user_id: referencia al usuario
        product_id: referencia al producto
        added_at: fecha en que el usuario agregó el producto
    """
    __tablename__ = "user_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="products")
    product: Mapped["Product"] = relationship(back_populates="user_products")