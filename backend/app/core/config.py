from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "TenderHub SA API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://tenderhub:tenderhub_dev@localhost:5432/tenderhub"
    secret_key: str = Field(default="development-only-secret-change-me-123456", min_length=32)
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
