import uuid
from typing_extensions import Self
from shared.schemas.characters import CharacterListIds
from .....core.use_cases import UseCaseProtocol 
from ...services.game.game import CharacterGameServiceProtocol 


class CharacterQuitAllFromGameUseCaseProtocol(UseCaseProtocol[CharacterListIds]):
    async def __call__(self: Self, user_id: uuid.UUID) -> CharacterListIds:
        ...


class CharacterQuitAllFromGameUseCase(CharacterQuitAllFromGameUseCaseProtocol):
    def __init__(self: Self, service: CharacterGameServiceProtocol):
        self.service = service

    async def __call__(self: Self, user_id: uuid.UUID) -> CharacterListIds:
        return await self.service.quit_all(user_id)
