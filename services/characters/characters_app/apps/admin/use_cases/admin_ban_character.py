import uuid
from typing import Protocol
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..repositories.admin_characters import AdminCharacterRepositoryProtocol
from ...characters.events.characters import CharacterEventsProtocol
from ..schemas import AdminCharacterReadSchema
from ....core.redis import get_redis_client


class AdminBanCharacterUseCaseProtocol(UseCaseProtocol[AdminCharacterReadSchema], Protocol):
    async def __call__(self: Self, character_id: uuid.UUID) -> AdminCharacterReadSchema: ...


class AdminBanCharacterUseCase(AdminBanCharacterUseCaseProtocol):
    def __init__(self: Self, repository: AdminCharacterRepositoryProtocol, character_events: CharacterEventsProtocol) -> None:
        self.repository = repository
        self.character_events = character_events

    async def __call__(self: Self, character_id: uuid.UUID) -> AdminCharacterReadSchema:
        character = await self.repository.set_banned(character_id, is_banned=True)
        if character is None:
            raise LookupError(f"Character {character_id} not found")
        
        # Добавляем в Redis blacklist с TTL 24 часа (время жизни access_token)
        redis_client = get_redis_client()
        await redis_client.setex(
            f"banned_character:{character.id}",
            86400,  # 24 часа в секундах
            "1"
        )
        
        # Публикуем событие бана
        await self.character_events.publish_character_banned(character.id, character.user_id)
        
        return AdminCharacterReadSchema.model_validate(character)
