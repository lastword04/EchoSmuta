from functools import lru_cache

import redis.asyncio as redis

from shared.services.templates import TextTemplateService
from ...settings import settings
from .events.economy import EconomyEvents
from .events.publisher import RedisPublisher
from .services.economy_templates import EconomyTemplateService


# Singleton template service
_template_service_instance: TextTemplateService | None = None


def get_text_template_service() -> TextTemplateService:
    global _template_service_instance
    if _template_service_instance is None:
        _template_service_instance = TextTemplateService(settings.system_messages_file_path)
    return _template_service_instance


@lru_cache
def get_redis_client() -> redis.Redis:
    redis_config = settings.redis
    if not redis_config:
        raise RuntimeError("Redis configuration is not set")
    
    # Парсим ssl как булево значение
    ssl_value = redis_config.get("ssl", False)
    if isinstance(ssl_value, str):
        ssl_value = ssl_value.lower() in ("true", "1", "yes")
    
    return redis.Redis(
        host=redis_config["host"],
        port=redis_config["port"],
        db=redis_config.get("db", 0),
        password=redis_config.get("password"),
        ssl=ssl_value,
        decode_responses=True,
        socket_connect_timeout=5,
    )


def get_redis_publisher() -> RedisPublisher:
    redis_client = get_redis_client()
    return RedisPublisher(redis_client)


def get_economy_events() -> EconomyEvents:
    publisher = get_redis_publisher()
    return EconomyEvents(publisher)


def get_economy_template_service() -> EconomyTemplateService:
    template_service = get_text_template_service()
    return EconomyTemplateService(template_service)