from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    BASE_URL: str = "http://localhost:8000"
    RATE_LIMIT_PER_MINUTE: int = 100
    CACHE_TTL_SECONDS: int = 3600


settings = Settings()
