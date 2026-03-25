"""
config.py
---------
Lee y valida las variables de entorno desde el archivo .env.
Expone un objeto 'settings' que se importa en todo el proyecto.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Cada atributo corresponde a una variable en el archivo .env.
    Pydantic valida que existan y tengan el tipo correcto al arrancar la app.
    """

    # Base de datos
    DATABASE_URL: str

    # Seguridad JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CoinGecko
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3"

    # Background job
    PRICE_FETCH_INTERVAL: int = 30

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,  # acepta DATABASE_URL o database_url indistintamente
    }


settings = Settings()