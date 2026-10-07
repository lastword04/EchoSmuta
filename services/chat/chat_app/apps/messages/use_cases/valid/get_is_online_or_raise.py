import logging

import redis.asyncio as redis
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.characters import CharacterOnlineStatus
from shared.exceptions import CharacterIsNotOnlineError
from typing_extensions import Self

from .....core.use_cases import UseCaseProtocol 
from ...adapter.characters import CharacterServiceClientProtocol

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 5
_CACHE_KEY_PREFIX = "chat:character-online:"


class GetIsOnlineCharacterOrRaiseUseCaseProtocol(UseCaseProtocol[CharacterOnlineStatus]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterOnlineStatus:
        ...


class GetIsOnlineCharacterOrRaiseUseCase(GetIsOnlineCharacterOrRaiseUseCaseProtocol):
    def __init__(
        self: Self,
        service: CharacterServiceClientProtocol,
        redis_client: redis.Redis,
    ):
        self.service = service
        self.redis = redis_client

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterOnlineStatus:
        if not token.character_id:
            raise CharacterIsNotOnlineError()

        cache_key = f"{_CACHE_KEY_PREFIX}{token.character_id}"
        status = await self._get_cached_status(cache_key)
        if status is None:
            status = await self.service.get_online_status_character(token.character_id)
            await self._cache_status(cache_key, status)

        if not status.is_online:
            raise CharacterIsNotOnlineError(token.character_id)

        return status

    async def _get_cached_status(self: Self, cache_key: str) -> CharacterOnlineStatus | None:
        try:
            cached_status = await self.redis.get(cache_key)
            if cached_status is None:
                return None
            if isinstance(cached_status, bytes):
                cached_status = cached_status.decode()
            return CharacterOnlineStatus.model_validate_json(cached_status)
        except Exception as error:
            logger.warning("Unable to read online status cache: %s", error)
            return None

    async def _cache_status(self: Self, cache_key: str, status: CharacterOnlineStatus) -> None:
        try:
            await self.redis.setex(
                cache_key,
                _CACHE_TTL_SECONDS,
                status.model_dump_json(),
            )
        except Exception as error:
            logger.warning("Unable to cache online status: %s", error)
