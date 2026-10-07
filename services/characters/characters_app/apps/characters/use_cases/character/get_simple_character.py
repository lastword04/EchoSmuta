import uuid
from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 
from shared.schemas.characters import CharacterSimpleReadSchema


class GetSimpleCharacterUseCaseProtocol(UseCaseProtocol[CharacterSimpleReadSchema]):
    async def __call__(self: Self, id: uuid.UUID) -> CharacterSimpleReadSchema:
        ...


class GetSimpleCharacterUseCase(GetSimpleCharacterUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self,  id: uuid.UUID) -> CharacterSimpleReadSchema:
        return await self.service.get_simple(id)
