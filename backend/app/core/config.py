from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "TenderHub SA API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://tenderhub:tenderhub_dev@localhost:5432/tenderhub"
    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    password_reset_expire_minutes: int = 30
    auth_rate_limit_per_minute: int = 10
    connector_timeout_seconds: float = 30
    connector_max_attempts: int = 3
    etenders_page_size: int = 100
    etenders_initial_sync_days: int = 30
    etenders_overlap_days: int = 1
    connector_schedule_enabled: bool = False
    connector_schedule_interval_minutes: int = 60
    public_app_url: str = "tenderhub://reset-password"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_starttls: bool = True
    notification_schedule_enabled: bool = False
    notification_schedule_interval_minutes: int = 60
    push_provider: str = "development"
    firebase_credentials_file: str | None = None
    mail_adapter: str = "development"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
