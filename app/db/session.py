"""
session.py
----------
Configura la conexión asíncrona a PostgreSQL usando SQLAlchemy 2.
Define el engine, la sesión y la clase Base de la que heredan los modelos.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


# Motor de base de datos asíncrono.
# echo=True imprime en consola cada query SQL ejecutada (útil en desarrollo).
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Fábrica de sesiones asíncronas.
# expire_on_commit=False evita que los objetos expiren al hacer commit,
# lo cual es importante en contextos async donde no puedes hacer lazy loading.
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Clase base de la que heredan todos los modelos.
    SQLAlchemy usa esta clase para registrar y crear las tablas.
    """
    pass


async def get_db():
    """
    Dependencia de FastAPI que provee una sesión de base de datos
    por cada request. Se usa con Depends() en los endpoints.

    Ejemplo:
        @router.get("/")
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()