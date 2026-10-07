import uuid
from typing import Protocol
from typing_extensions import Self
from ..repositories.admin_characters import AdminCharacterRepositoryProtocol
from ...characters.events.characters import CharacterEventsProtocol
from ..schemas import AdminCharacterReadSchema
from ....core.redis import get_redis_client


class AdminUnbanAllByUserUseCaseProtocol(Protocol):
    async def __call__(self: Self, user_id: uuid.UUID) -> list[AdminCharacterReadSchema]: ...


class AdminUnbanAllByUserUseCase(AdminUnbanAllByUserUseCaseProtocol):
    def __init__(self: Self, repository: AdminCharacterRepositoryProtocol, character_events: CharacterEventsProtocol) -> None:
        self.repository = repository
        self.character_events = character_events

    async def __call__(self: Self, user_id: uuid.UUID) -> list[AdminCharacterReadSchema]:
        characters = await self.repository.set_banned_by_user(user_id, is_banned=False)
        if not characters:
            raise LookupError(f"No characters found for user {user_id}")

        redis_client = get_redis_client()
        for character in characters:
            await redis_client.delete(f"banned_character:{character.id}")
            await self.character_events.publish_character_unbanned(character.id, character.user_id)

        return [AdminCharacterReadSchema.model_validate(c) for c in characters]
