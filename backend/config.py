from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    app_name: str = "KisanSetu API"
    environment: str = "development"
    database_url: str = "sqlite:///./kisansetu.db"
    cors_origins: str = "http://localhost:8081,http://localhost:19006"
    # These defaults are intentionally usable only for local development.
    operator_access_token: str = "local-operator"
    auth_secret_key: str = "development-only-change-me"
    otp_request_limit: int = 5
    otp_verify_limit: int = 10
    otp_rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.environment.strip().lower() != "development":
            if self.operator_access_token == "local-operator" or len(self.operator_access_token) < 16:
                raise ValueError("OPERATOR_ACCESS_TOKEN must be explicitly set to a long random value outside development")
            if self.auth_secret_key == "development-only-change-me" or len(self.auth_secret_key) < 32:
                raise ValueError("AUTH_SECRET_KEY must be explicitly set to a 32+ character random value outside development")
        if min(self.otp_request_limit, self.otp_verify_limit, self.otp_rate_limit_window_seconds) <= 0:
            raise ValueError("OTP rate limit settings must be positive")
        return self

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
