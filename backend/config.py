from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KisanSetu API"
    environment: str = "development"
    database_url: str = "sqlite:///./kisansetu.db"
    cors_origins: str = "http://localhost:8081,http://localhost:19006"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def database_path() -> Path:
    url = get_settings().database_url
    prefix = "sqlite:///"
    if url.startswith(prefix):
        return Path(url.removeprefix(prefix))
    return Path("kisansetu.db")
