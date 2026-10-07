import uuid
from typing_extensions import Self
from shared.schemas.characters import CharacterReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.game.game import CharacterGameServiceProtocol 


class CharacterJoinToGameUseCaseProtocol(UseCaseProtocol[CharacterReadSchema]):
    async def __call__(self: Self, character_id: uuid.UUID, user_id: uuid.UUID) -> CharacterReadSchema:
        ...


class CharacterJoinToGameUseCase(CharacterJoinToGameUseCaseProtocol):
    def __init__(self: Self, service: CharacterGameServiceProtocol):
        self.service = service

    async def __call__(self: Self, character_id: uuid.UUID, user_id: uuid.UUID) -> CharacterReadSchema:
        return await self.service.join(user_id, character_id)
