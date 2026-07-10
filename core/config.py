"""Ilova sozlamalari (.env dan o'qiladi)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Manager bot
    manager_bot_token: str = Field(alias="MANAGER_BOT_TOKEN")
    manager_webhook_secret: str = Field(alias="MANAGER_WEBHOOK_SECRET")

    # Web / webhook
    domain: str = Field(alias="DOMAIN")
    webapp_host: str = Field(default="0.0.0.0", alias="WEBAPP_HOST")
    webapp_port: int = Field(default=8080, alias="WEBAPP_PORT")

    # Infra
    db_url: str = Field(alias="DB_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Security
    fernet_key: str = Field(alias="FERNET_KEY")
    super_admins: str = Field(default="", alias="SUPER_ADMINS")
    force_sub_channels: str = Field(default="", alias="FORCE_SUB_CHANNELS")

    # Env
    env: str = Field(default="development", alias="ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def super_admin_ids(self) -> list[int]:
        return [int(x) for x in self.super_admins.split(",") if x.strip()]

    @property
    def force_sub_list(self) -> list[str]:
        return [x.strip() for x in self.force_sub_channels.split(",") if x.strip()]

    @property
    def manager_webhook_path(self) -> str:
        return f"/wh/manager/{self.manager_webhook_secret}"

    @property
    def manager_webhook_url(self) -> str:
        return f"{self.domain.rstrip('/')}{self.manager_webhook_path}"

    def child_webhook_url(self, secret: str) -> str:
        return f"{self.domain.rstrip('/')}/wh/child/{secret}"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
