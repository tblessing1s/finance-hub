from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Every value can be overridden by an environment variable."""

    model_config = SettingsConfigDict(env_prefix="HUB_", env_file=".env", extra="ignore")

    # HUB_DATABASE_URL locally; DATABASE_URL is what `fly postgres attach` sets.
    database_url: str = Field(
        default="postgresql+psycopg://hub:hub@localhost:5432/finance_hub",
        validation_alias=AliasChoices("HUB_DATABASE_URL", "DATABASE_URL"),
    )
    test_database_url: str = "postgresql+psycopg://hub:hub@localhost:5432/finance_hub_test"
    cors_origins: list[str] = ["http://localhost:4200"]
    # Directory of the built Angular app. Unset in development (ng serve proxies /api instead).
    static_dir: str | None = None
    # "user:password". When set, every request must carry matching HTTP Basic credentials.
    basic_auth: str | None = None

    @field_validator("database_url", "test_database_url", mode="before")
    @classmethod
    def _psycopg_scheme(cls, url: str) -> str:
        """Accept the bare postgres:// scheme Fly and Heroku emit; SQLAlchemy needs the driver."""
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
