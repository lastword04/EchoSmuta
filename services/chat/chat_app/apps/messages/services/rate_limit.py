import redis.asyncio as redis
import uuid
import time
from typing import Protocol


class RateLimitServiceProtocol(Protocol):
    async def is_allowed(self, character_id: uuid.UUID) -> bool:
        ...


class RateLimitService(RateLimitServiceProtocol):
    def __init__(self, redis_client: redis.Redis, cooldown: float = 1.0):
        self.redis = redis_client
        self.cooldown = cooldown

    async def is_allowed(self, character_id: uuid.UUID) -> bool:
        key = f"chat:cooldown:{character_id}"
        current_time = time.time()
        
        last_time_str = await self.redis.get(key)
        last_time = float(last_time_str) if last_time_str else 0
        
        if current_time - last_time < self.cooldown:
            return False
        
        await self.redis.setex(key, int(self.cooldown) + 1, str(current_time))
        return True