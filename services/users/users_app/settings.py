import os
from typing import Annotated, List

from fastapi import Depends
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode

__all__ = (
    "get_settings",
    "Settings",
    "settings",
)


class Db(BaseModel):
    """
    Настройки для подключения к базе данных.
    """

    host: str
    port: int
    user: str
    password: str
    name: str
    scheme: str = "public"

    provider: str = "postgresql+psycopg_async"

    @property
    def dsn(self) -> str:
        return f"{self.provider}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class JWTSettings(BaseModel):
    """
    Настройки JWT.
    """

    secret_key: str
    algorithm: str = "HS256"
    expire_minutes: int = 24


class Settings(BaseSettings):
    """
    Настройки модели.
    """

    debug: bool
    base_url: str
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service_name: str = "user-service"
    secret_key: str
    cors_origins: Annotated[List[str], NoDecode]
    service_jwt: JWTSettings

    user_access_token: JWTSettings

    @field_validator("cors_origins", mode="before")
    @classmethod
    def decode_cors_origins(cls, v: str) -> List[str]:
        return v.split(",")

    db: Db

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
        env_prefix="USERS_SERVICE_APP_",
    )


def get_settings():
    return Settings()  # type: ignore


settings = get_settings()

SettingsService = Annotated[Settings, Depends(get_settings)]
