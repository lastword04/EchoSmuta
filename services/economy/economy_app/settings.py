import os
from typing import Annotated, List

from fastapi import Depends
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode


class DbSettings(BaseModel):
    host: str
    port: int
    user: str
    password: str
    name: str
    scheme: str = "public"
    provider: str = "postgresql+asyncpg"

    @property
    def dsn(self) -> str:
        return f"{self.provider}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class JwtSettings(BaseModel):
    secret_key: str
    algorithm: str = "HS256"
    expire_minutes: int = 1440


class ServiceClientSettings(BaseModel):
    base_url: str
    service_token: str | None = None
    timeout: float = 10.0

class PricingSettings(BaseModel):
    scheduler_enabled: bool = True
    scheduler_check_interval_seconds: int = 60
    recalculation_lock_minutes: int = 30
    recalculation_retry_minutes: int = 5
    recalculation_min_hours: float = 18.0
    recalculation_max_hours: float = 32.0
    price_floor_multiplier: float = 0.2    
    price_ceiling_multiplier: float = 5.0   
    

class Settings(BaseSettings):
    debug: bool = False
    service_name: str = "economy-service"
    service_jwt: JwtSettings
    user_access_token: JwtSettings
    db: DbSettings

    # CORS настройка (как в characters)
    cors_origins: Annotated[List[str], NoDecode]

    # Внутренние клиенты
    characters_service: ServiceClientSettings
    mining_service: ServiceClientSettings
    pricing: PricingSettings

    # Путь к файлу системных сообщений
    system_messages_file_path: str

    # Локация ломбарда — для админских/шедулерных событий экономики
    pawn_shop_location_slug: str = "1.26.pawn-shop"

    # Локация Харчевни — для покупки еды
    tavern_location_slug: str = "1.15.tavern"

    # Redis и Celery (опционально)
    redis: dict | None = None
    celery: dict | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def decode_cors_origins(cls, v: str) -> List[str]:
        return v.split(",")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ECONOMY_SERVICE_APP_",
        env_nested_delimiter="__",
        extra="ignore",
    )

settings = Settings()