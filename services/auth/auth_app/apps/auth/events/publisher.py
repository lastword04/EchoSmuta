import json
import logging
from typing import Protocol
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisPublisherProtocol(Protocol):
    async def publish(self, channel: str, message: dict) -> None: ...

class RedisPublisher(RedisPublisherProtocol):
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def publish(self, channel: str, message: dict) -> None:
        """Публикация сообщения в Redis канал"""
        try:
            await self.redis.publish(channel, json.dumps(message))
            logger.debug(f"Published to {channel}: {message}")
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            raise