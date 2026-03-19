from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3"
    PRICE_FETCH_INTERVAL: int = 30

    class Config:
        env_file = ".env"


settings = Settings()