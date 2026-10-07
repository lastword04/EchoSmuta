import os
from typing import Annotated, List, Any
from fastapi import Depends
from pydantic import BaseModel, field_validator, model_validator
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

class JWTSettings(BaseModel):
    """
    Настройки JWT.
    """

    secret_key: str
    algorithm: str = 'HS256'
    expire_minutes: int = 24 * 60

class CharacterServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8082'

class CategorySettings(BaseModel):
    limit: int = 5
    main_max_count_characters: int = 30
    not_main_max_count_characters: int = 20

class FilterSmylesSettings(BaseModel):
    max_smyles: int = 3

class FilterLinksSettings(BaseModel):
    allowed_hosts: set[str] = set()

class Settings(BaseSettings):
    """
    Настройки модели.
    """

    debug: bool
    base_url: str
    frontend_url: str = 'http://localhost:5173'
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service_name: str
    secret_key: str
    cors_origins: Annotated[List[str], NoDecode]

    
    service_jwt: JWTSettings

    token_refresh_buffer_minutes: int
    
    user_access_token: JWTSettings

    character_service_app: CharacterServiceAppConfig

    valid_rooms: Annotated[List[str], NoDecode]

    cooldown: float

    category: CategorySettings

    filter_smyles: FilterSmylesSettings
    filter_links: FilterLinksSettings

    system_messages_file_path: str
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def decode_cors_origins(cls, v: str) -> List[str]:
        return v.split(',')
    
    @field_validator('valid_rooms', mode='before')
    @classmethod
    def decode_valid_rooms(cls, v: str) -> List[str]:
        return v.split(',')
    
    db: Db

    redis: RedisSettings

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
        env_prefix='CHAT_SERVICE_APP_',
    )



def get_settings():
    return Settings()


settings = get_settings()

SettingsService = Annotated[Settings, Depends(get_settings)]