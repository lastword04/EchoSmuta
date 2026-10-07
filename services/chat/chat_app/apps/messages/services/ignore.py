import redis.asyncio as redis
import time
import uuid
from typing import Protocol, Optional
from typing_extensions import Self
from ..repositories.ignore import IgnoreRepositoryProtocol
from ..schemas import IgnoreCreateSchema, IgnoreReadSchema, IgnoreRequestSchema
from ..exceptions import CannotIgnoreSelfError, IgnoreCooldownError


class RateLimitIgnoreServiceProtocol(Protocol):
    redis_client: redis.Redis
    cooldown: float
    
    async def is_allowed(self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> bool:
        ...

    async def get_remaining_time(self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> float:
        ...

    async def update_last_action(self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> None:
        ...


class RateLimitIgnoreService(RateLimitIgnoreServiceProtocol):
    def __init__(self, redis_client: redis.Redis, cooldown: float = 60.0):
        self.redis = redis_client
        self.cooldown = cooldown

    async def is_allowed(self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> bool:
        remaining_time = await self.get_remaining_time(character_id, ignored_character_id)
        return remaining_time <= 0

    async def get_remaining_time(self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> float:
        key = f"ignore:cooldown:{character_id}:{ignored_character_id}"
        current_time = time.time()

        last_time_str = await self.redis.get(key)
        last_time = float(last_time_str) if last_time_str else 0

        elapsed_time = current_time - last_time
        remaining_time = self.cooldown - elapsed_time
        return max(0, remaining_time)

    async def update_last_action(self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> None:
        key = f"ignore:cooldown:{character_id}:{ignored_character_id}"
        current_time = time.time()
        await self.redis.setex(key, int(self.cooldown) + 1, str(current_time))


class IgnoreServiceProtocol(Protocol):
    async def create(self: Self, character_id: uuid.UUID, data: IgnoreCreateSchema) -> IgnoreReadSchema:
        ...

    async def delete(self: Self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> bool:
        ...

    async def get_ignored_characters(self: Self, character_id: uuid.UUID, other_character_ids: list[uuid.UUID]) -> dict[uuid.UUID, bool]:
        ...


class IgnoreService(IgnoreServiceProtocol):
    def __init__(self: Self, repository: IgnoreRepositoryProtocol,
                 rate_limit_ignore_service: RateLimitIgnoreServiceProtocol):
        self.repository = repository
        self.rate_limit_ignore_service = rate_limit_ignore_service

    async def create(self: Self, character_id: uuid.UUID, data: IgnoreRequestSchema) -> IgnoreReadSchema:
        if character_id == data.ignored_character_id:
            raise CannotIgnoreSelfError(character_id=character_id)
        
        remaining_time = await self.rate_limit_ignore_service.get_remaining_time(character_id, data.ignored_character_id)
        if remaining_time > 0:
            raise IgnoreCooldownError(
                character_id=character_id, 
                cooldown=self.rate_limit_ignore_service.cooldown,
                remaining_time=remaining_time
            )
        
        data = IgnoreCreateSchema(character_id=character_id, **data.model_dump())
        result = await self.repository.create(data)

        await self.rate_limit_ignore_service.update_last_action(character_id, data.ignored_character_id)

        return result

    async def delete(self: Self, character_id: uuid.UUID, ignored_character_id: uuid.UUID) -> bool:
        remaining_time = await self.rate_limit_ignore_service.get_remaining_time(character_id, ignored_character_id)
        if remaining_time > 0:
            raise IgnoreCooldownError(
                character_id=character_id, 
                cooldown=self.rate_limit_ignore_service.cooldown,
                remaining_time=remaining_time
            )
        
        result = await self.repository.delete(character_id, ignored_character_id)

        await self.rate_limit_ignore_service.update_last_action(character_id, ignored_character_id)

        return result

    async def get_ignored_characters(self: Self, character_id: uuid.UUID, other_character_ids: list[uuid.UUID]) -> dict[uuid.UUID, bool]:
        return await self.repository.get_ignored_characters(character_id, other_character_ids)


