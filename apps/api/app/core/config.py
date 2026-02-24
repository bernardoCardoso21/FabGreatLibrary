from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API
    api_port: int = 8000
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://fab:fab@localhost:5432/fabgreat"
    # Set to True in production when Postgres requires SSL
    database_ssl: bool = False

    # JWT
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Card dataset (the-fab-cube/flesh-and-blood-cards release tag)
    cards_data_version: str = "v8.1.0"


settings = Settings()
