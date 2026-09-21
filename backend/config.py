from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    cors_origins: str = "http://localhost:5173"
    app_title: str = "Creditos API"
    app_version: str = "0.2.0"

    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def sqlalchemy_database_url(self) -> str:
        database_url = self.database_url
        if not database_url:
            raise RuntimeError(
                "Define DATABASE_URL before using the PostgreSQL connection"
            )

        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if database_url.startswith("postgresql://"):
            return database_url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )
        return database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
