import uuid
from typing_extensions import Self
from shared.schemas.characters import CharacterReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.game.game import CharacterGameServiceProtocol 


class CharacterJoinMainToGameUseCaseProtocol(UseCaseProtocol[CharacterReadSchema]):
    async def __call__(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        ...


class CharacterJoinMainToGameUseCase(CharacterJoinMainToGameUseCaseProtocol):
    def __init__(self: Self, service: CharacterGameServiceProtocol):
        self.service = service

    async def __call__(self: Self, user_id: uuid.UUID) -> CharacterReadSchema:
        return await self.service.join_main(user_id)
