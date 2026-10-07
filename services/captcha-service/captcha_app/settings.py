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


class JWTSettings(BaseModel):
    """
    Настройки JWT.
    """

    secret_key: str
    algorithm: str = 'HS256'
    expire_minutes: int = 1440


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


class ImageSettings(BaseSettings):
    font_path: str

class Settings(BaseSettings):
    """
    Настройки модели.
    """

    debug: bool
    base_url: str
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    secret_key: str
    cors_origins: Annotated[List[str], NoDecode] 
    service_jwt: JWTSettings

    service_name: str = 'captcha-service'

    @field_validator('cors_origins', mode='before')
    @classmethod
    def decode_cors_origins(cls, v: str) -> List[str]:
        return v.split(',')
    
    image: ImageSettings

    redis: RedisSettings

    redis_ttl: int = 5 * 60  # 5 минут

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
        env_prefix='CAPTCHA_SERVICE_APP_',
    )


def get_settings():
    return Settings()  # type: ignore


settings = get_settings()

SettingsService = Annotated[Settings, Depends(get_settings)]