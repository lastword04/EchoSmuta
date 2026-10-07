import os
from typing import Annotated, List
from fastapi import Depends
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode

__all__ = (
    'get_settings',
    'Settings',
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
    
class CelerySettings(BaseSettings):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"
    redbeat_redis_url: str = "redis://localhost:6380/1"
    timezone: str = "UTC"
    cleanup_reset_token_cron_hour: int = 3
    cleanup_reset_token_cron_minute: int = 0
    cleanup_refresh_token_cron_hour: int = 4
    cleanup_refresh_token_cron_minute: int = 0

class JWTSettings(BaseModel):
    """
    Настройки JWT.
    """

    secret_key: str
    algorithm: str = 'HS256'
    expire_minutes: int = 24 * 60


class RefreshTokenSettings(BaseModel):
    """
    Настройки для рефреш токенов.
    """

    expire_minutes: int = 7 * 24 * 60


class ResetTokenSettings(BaseModel):
    """
    Настройки для токенов сброса пароля.
    """

    expire_minutes: int = 60


class UserServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8081'


class CharacterServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8082'

class EmailServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8083'

class CaptchaServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8085'

class Settings(BaseSettings):
    """
    Настройки модели.
    """

    debug: bool
    base_url: str
    frontend_url: str = 'http://localhost:3000'
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service_name: str
    secret_key: str
    cors_origins: Annotated[List[str], NoDecode]
    trusted_hosts: Annotated[List[str], NoDecode]
    
    service_jwt: JWTSettings

    token_refresh_buffer_minutes: int
    
    user_access_token: JWTSettings
    refresh_token: RefreshTokenSettings
    reset_token: ResetTokenSettings

    user_service_app: UserServiceAppConfig
    character_service_app: CharacterServiceAppConfig
    email_service_app: EmailServiceAppConfig
    captcha_service_app: CaptchaServiceAppConfig


    @field_validator('cors_origins', mode='before')
    @classmethod
    def decode_cors_origins(cls, v: str) -> List[str]:
        return v.split(',')

    @field_validator('trusted_hosts', mode='before')
    @classmethod
    def decode_trusted_hosts(cls, v: str) -> List[str]:
        return v.split(',')
    
    db: Db

    redis: RedisSettings

    celery: CelerySettings = CelerySettings()

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
        env_prefix='AUTH_SERVICE_APP_',
    )


def get_settings():
    return Settings()  # type: ignore


settings = get_settings()

SettingsService = Annotated[Settings, Depends(get_settings)]