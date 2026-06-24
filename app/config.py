from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    BASE_URL: str = "http://localhost:8000"
    RATE_LIMIT_PER_MINUTE: int = 100
    REDIRECT_RATE_LIMIT_PER_MINUTE: int = 1000
    CACHE_TTL_SECONDS: int = 3600
    # Comma-separated origins, e.g.: https://myapp.com,https://www.myapp.com
    ALLOWED_ORIGINS: str = ""

    @property
    def origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list, stripping blanks."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
