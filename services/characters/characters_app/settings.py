import os
from pathlib import Path
from typing import Annotated, List

from fastapi import Depends
from pydantic import BaseModel, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode

__all__ = (
    'get_settings',
    'Settings',
    'settings',
)

_BASE_DIR = Path(__file__).resolve().parents[1]


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

    provider: str = 'postgresql+asyncpg'

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

class HumanSettings(BaseModel):
    """
    Настройки для расы человека.
    """
    base_power: int = 4
    base_agility: int = 4
    base_lucky: int = 5

class ElfSettings(BaseModel):
    """
    Настройки для расы эльфа.
    """
    base_power: int = 4
    base_agility: int = 5
    base_lucky: int = 4

class OrcSettings(BaseModel):
    """
    Настройки для расы орка.
    """
    base_power: int = 5
    base_agility: int = 4
    base_lucky: int = 4


class RaceSettings(BaseModel):
    """
    Настройки для расы персонажа.
    """
    human: HumanSettings
    elf: ElfSettings
    orc: OrcSettings


class GlobalCharacterSettings(BaseModel):
    default_experience: int = 0
    default_level: int = 0
    default_health: int = 30
    default_max_health: int = 30
    default_tiredness: float = 0.0
    default_max_tiredness: float = 1.0
    default_endurance: int = 5
    default_weight: int = 0
    default_max_weight: int = 100
    default_mana: int = 10
    default_max_mana: int = 10
    default_intelligence: int = 0
    default_weight: int = 0
    default_max_weight: int = 0
    default_gold: float = 0.0
    default_ducats: float = 3.0
    health_multiplier: float = 6.0
    mana_multiplier: float = 1.0
    max_characters_on_user: int = 4



class CharacterAttachmentSettings(BaseModel):
    attach_cost: int = 10
    detach_cost: int = 1000
    attach_cost_per_level: int = 5
    detach_cost_per_level: int = 500

class TransferValueCharactersSettings(BaseModel):
    min_transfer_level: int = 0
    min_transfer_ducats: float = 1000.0
    min_transfer_gold: float = 5.0
    transfer_tax_percentage: float = 0.1

class CharacterSettings(BaseModel):
    deactivation_period_days: int = 30
    inactive_time_minutes: int = 24 * 60

class CharacterActivitySettings(BaseModel):
    delete_after_minutes: int = 30 * 24 * 60

class ExchangeSettings(BaseModel):
    min_ducats_on_slot: int = 1
    max_ducats_on_slot: int = 100
    min_gold_on_slot: int = 1
    max_gold_on_slot: int = 100
    min_course_on_gold: int = 1
    max_course_on_gold: int = 100
    seller_on_ducats_tax: float = 0.05

class CelerySettings(BaseSettings):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"
    redbeat_redis_url: str = "redis://localhost:6380/1"
    timezone: str = "UTC"
    cleanup_detached_characters_cron_hour: int = 0
    cleanup_detached_characters_cron_minute: int = 0
    cleanup_detached_characters_cron_day: int = 0

    cleanup_old_character_activity_cron_hour: int = 0
    cleanup_old_character_activity_cron_minute: int = 0
    cleanup_old_character_activity_cron_day: int = 0

    change_status_characters_cron_hour: str = "0,12"
    change_status_characters_cron_minute: int = 0



class JWTSettings(BaseModel):
    """
    Настройки JWT.
    """

    secret_key: str
    algorithm: str = 'HS256'
    expire_minutes: int = 1440


class FileServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8084'

class ChatServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8087'

class CategoryServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8087'

class UsersServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8081'
class MiningServiceAppConfig(BaseModel):
    base_url: str = 'http://localhost:8088'

class Settings(BaseSettings):
    """
    Настройки модели.
    """

    debug: bool
    base_url: str
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_url: HttpUrl = 'http://localhost:5137'

    secret_key: str
    cors_origins: Annotated[List[str], NoDecode] 
    service_jwt: JWTSettings

    token_refresh_buffer_minutes: int

    user_access_token: JWTSettings
    
    race_settings: RaceSettings
    global_character_settings: GlobalCharacterSettings
    character_attachment_settings: CharacterAttachmentSettings
    transfer_value_characters_settings: TransferValueCharactersSettings
    character_settings: CharacterSettings
    character_activity_settings: CharacterActivitySettings
    exchange_settings: ExchangeSettings
    
    service_name: str = 'character-service'

    file_service_app: FileServiceAppConfig
    chat_service_app: ChatServiceAppConfig
    category_service_app: CategoryServiceAppConfig
    users_service_app: UsersServiceAppConfig
    mining_service_app: MiningServiceAppConfig

    @field_validator('cors_origins', mode='before')
    @classmethod
    def decode_cors_origins(cls, v: str) -> List[str]:
        return v.split(',')
   

    db: Db

    redis: RedisSettings

    celery: CelerySettings

    # Rest (гостиница)
    rest_location_slug: str = "1.12.inn"
    rest_max_rooms: int = 3000
    rest_discount_coefficient: float = 0.05
    rest_health_multiplier: float = 2.0
    rest_tiredness_multiplier: float = 2.0
    rest_mana_multiplier: float = 1.0
    rest_inn_name: str = "Уставшая Душа"
    system_messages_file_path: str = str(_BASE_DIR / "shared" / "system_messages.json")

    # Houses (частные дома)
    residential_location_slug: str = "1.19.residential-area"
    house_price_ducats: int = 1000
    house_capacity: int = 450
    house_max_guests: int = 10
    # Wear (износ мебели в доме)
    house_wear_tick_seconds: int = 60        # период тика задачи износа
    house_wear_rate_minutes: float = 10.0    # минут работы одного пользователя = +1 wear

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
        env_prefix='CHARACTER_SERVICE_APP_',
    )


def get_settings():
    return Settings()  # type: ignore


settings = get_settings()

SettingsService = Annotated[Settings, Depends(get_settings)]