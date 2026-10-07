import os
from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, HttpUrl, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

__all__ = (
    'Settings',
    'get_settings',
    'settings',
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
    scheme: str = 'public'

    provider: str = 'postgresql+psycopg_async'

    @property
    def dsn(self) -> str:
        return f'{self.provider}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}'

    @property
    def dsn_sync(self) -> str:
        # Преобразуем асинхронный DSN в синхронный, используя драйвер psycopg (версия 3)
        dsn = self.dsn
        # Заменяем асинхронный драйвер на синхронный
        dsn = dsn.replace('+psycopg_async', '+psycopg')
        dsn = dsn.replace('+asyncpg', '+psycopg')
        # Если вдруг осталось просто postgresql:// без драйвера, добавляем
        if dsn.startswith('postgresql://') and '+psycopg' not in dsn:
            dsn = dsn.replace('postgresql://', 'postgresql+psycopg://')
        return dsn


class JWTSettings(BaseModel):
    """
    Настройки JWT.
    """

    secret_key: str
    algorithm: str = 'HS256'
    expire_minutes: int = 1440


class CaptchaServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8085'

class FileServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8084'

class MiningConfig(BaseModel):
    cooldown_seconds: int = 180  # 3 minutes
    min_valid_character_level: int = 3
    max_valid_character_tiredness: float = 0.495
    change_tiredness: float = 0.03
    min_attack_monster_health_percentage: float = 0.70
    min_attack_monster_tiredness: float = 0.25
    default_monster_attack_chance: float = 0.15
    default_attack_monster_standart: float = 0.75

class ItemsCreatingConfig(BaseModel):
    cooldown_seconds: int = 180  # 3 minutes
    min_valid_character_level: int = 3  
    max_valid_character_tiredness: float = 0.49
    change_tiredness: float = 0.03    
    chance_lose_resource: float = 0.2  # 20% chance to lose resource on failure

class CityTradingShopConfig(BaseModel):
    license_renewal_cost: int = 15
    license_renewal_days: int = 14


class TradeLicenseConfig(BaseModel):
    renewal_cost: int = 15
    renewal_days: int = 14
    deal_tax: float = 0.10
    deal_tax_discounted: float = 0.03
    exchange_tax: float = 0.15
    exchange_tax_discounted: float = 0.05

class CharacterServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8082/api/characters'
    stats_base_url: str = 'http://localhost:8082/api/stats'


class AdminConfig(BaseModel):
    max_stack: int = 9999


class CelerySettings(BaseSettings):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"
    redbeat_redis_url: str = "redis://localhost:6380/1"
    timezone: str = "UTC"

class RedisSettings(BaseModel):
    """
    Настройки для подключения к Redis.
    """

    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: str | None = None
    ssl: bool = False
    encoding: str = 'utf-8'
    decode_responses: bool = True

    def to_connection_kwargs(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": self.password,
            "ssl": self.ssl,
            "encoding": self.encoding,
            "decode_responses": self.decode_responses,
        }

class Settings(BaseSettings):
    """
    Настройки модели.
    """

    debug: bool
    base_url: str
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_url: HttpUrl = 'http://localhost:5137'

    secret_key: str
    cors_origins: Annotated[list[str], NoDecode] 
    service_jwt: JWTSettings

    token_refresh_buffer_minutes: int

    user_access_token: JWTSettings
    
    service_name: str = 'mining-service'

    mining: MiningConfig
    items_creating: ItemsCreatingConfig
    city_trading_shop: CityTradingShopConfig
    trade_license: TradeLicenseConfig = TradeLicenseConfig()
    admin: AdminConfig = AdminConfig()

    character_service_app: CharacterServiceAppConfig
    captcha_service_app: CaptchaServiceAppConfig
    file_service_app: FileServiceAppConfig


    system_messages_file_path: str

    @field_validator('cors_origins', mode='before')
    @classmethod
    def decode_cors_origins(cls, v: str) -> list[str]:
        return v.split(',')

    db: Db

    redis: RedisSettings

    celery: CelerySettings

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
        env_prefix='MINING_SERVICE_APP_',
    )


def get_settings():
    return Settings()  # type: ignore


settings = get_settings()

SettingsService = Annotated[Settings, Depends(get_settings)]
