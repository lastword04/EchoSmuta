import json
import logging
from typing import Protocol

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisPublisherProtocol(Protocol):
    async def publish(self, channel: str, message: dict) -> None: ...
    async def close(self) -> None: ...

class RedisPublisher(RedisPublisherProtocol):
    def __init__(self, redis_client: redis.Redis, *, owns_client: bool = False):
        self.redis = redis_client
        self._owns_client = owns_client  # ← флаг: "этот клиент мой, я его закрою"
    
    async def publish(self, channel: str, message: dict) -> None:
        """Публикация сообщения в Redis канал"""
        try:
            await self.redis.publish(channel, json.dumps(message))
            logger.debug(f"Published to {channel}: {message}")
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            raise
    
    async def close(self) -> None:
        """Закрываем клиент ТОЛЬКО если мы его создали сами"""
        if self._owns_client:
            try:
                await self.redis.aclose()
                logger.debug("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        # Если клиент глобальный — НЕ ТРОГАЕМ ЕГО. 
        # Его закроет close_redis_client() при shutdown приложения.
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()