import redis.asyncio as redis
from fastapi import Depends

from ...core.redis import get_redis_client
from ...settings import Settings, get_settings
from .adapter.characters import CharacterServiceClient, CharacterServiceClientProtocol
from .use_cases.valid.get_is_online_or_raise import GetIsOnlineCharacterOrRaiseUseCaseProtocol, GetIsOnlineCharacterOrRaiseUseCase 

def get_character_adapter(settings: Settings = Depends(get_settings)) -> CharacterServiceClientProtocol:
    return CharacterServiceClient(base_url=settings.character_service_app.base_url)

def get_valid_status_character_use_case(
        service: CharacterServiceClientProtocol = Depends(get_character_adapter),
        redis_client: redis.Redis = Depends(get_redis_client),
) -> GetIsOnlineCharacterOrRaiseUseCaseProtocol:
    return GetIsOnlineCharacterOrRaiseUseCase(service, redis_client)
