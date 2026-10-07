import logging

import redis.asyncio as redis

from ..settings import settings

logger = logging.getLogger(__name__)

# Глобальный экземпляр клиента (опционально)
_redis_client: redis.Redis | None = None

def get_redis_client() -> redis.Redis:
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        connection_kwargs = settings.redis.to_connection_kwargs()
        # 👇 Добавляем настройки пула, если их нет
        connection_kwargs.setdefault("max_connections", 20)
        connection_kwargs.setdefault("decode_responses", True)
        
        _redis_client = redis.Redis(**connection_kwargs)
        logger.info(f"Redis client created: {settings.redis.host}:{settings.redis.port}/{settings.redis.db}")
        return _redis_client
    except Exception as e:
        logger.error(f"Failed to create Redis client: {e}")
        raise

async def close_redis_client() -> None:
    """Закрывает Redis клиент"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")