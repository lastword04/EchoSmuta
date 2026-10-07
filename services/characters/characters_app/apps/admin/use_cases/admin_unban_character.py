import uuid
from typing import Protocol
from typing_extensions import Self
from ....core.use_cases import UseCaseProtocol
from ..repositories.admin_characters import AdminCharacterRepositoryProtocol
from ...characters.events.characters import CharacterEventsProtocol
from ..schemas import AdminCharacterReadSchema
from ....core.redis import get_redis_client


class AdminUnbanCharacterUseCaseProtocol(UseCaseProtocol[AdminCharacterReadSchema], Protocol):
    async def __call__(self: Self, character_id: uuid.UUID) -> AdminCharacterReadSchema: ...


class AdminUnbanCharacterUseCase(AdminUnbanCharacterUseCaseProtocol):
    def __init__(self: Self, repository: AdminCharacterRepositoryProtocol, character_events: CharacterEventsProtocol) -> None:
        self.repository = repository
        self.character_events = character_events

    async def __call__(self: Self, character_id: uuid.UUID) -> AdminCharacterReadSchema:
        character = await self.repository.set_banned(character_id, is_banned=False)
        if character is None:
            raise LookupError(f"Character {character_id} not found")
        
        # Удаляем из Redis blacklist
        redis_client = get_redis_client()
        await redis_client.delete(f"banned_character:{character.id}")
        
        # Публикуем событие разбана
        await self.character_events.publish_character_unbanned(character.id, character.user_id)
        
        return AdminCharacterReadSchema.model_validate(character)
