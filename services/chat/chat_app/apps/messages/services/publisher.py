import redis.asyncio as redis
import json
from typing import Protocol


class RedisPublisherProtocol(Protocol):
    async def publish_to_room(self, room: str, message: dict) -> None: ...
    async def publish(self, channel: str, message: dict) -> None: ...
    async def close(self) -> None: ...


class RedisPublisher(RedisPublisherProtocol):
    def __init__(self, redis_client: redis.Redis, *, owns_client: bool = False):
        self.redis = redis_client
        self._owns_client = owns_client

    async def publish_to_room(self, room: str, message: dict):
        """Публикация в канал с префиксом chat_room_"""
        await self.redis.publish(f"chat_room_{room}", json.dumps(message))

    async def publish(self, channel: str, message: dict):
        """Публикация в произвольный канал (без префикса)"""
        await self.redis.publish(channel, json.dumps(message))
    
    async def close(self) -> None:
        """Закрываем клиент ТОЛЬКО если мы его создали сами"""
        if self._owns_client:
            try:
                await self.redis.aclose()
            except Exception as e:
                print(f"Error closing Redis: {e}")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()