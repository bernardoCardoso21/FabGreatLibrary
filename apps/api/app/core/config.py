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

    # JWT
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30


settings = Settings()
