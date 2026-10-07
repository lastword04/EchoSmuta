from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 
from shared.schemas.characters import CharacterSimpleReadSchema


class GetByNameCharacterUseCaseProtocol(UseCaseProtocol[CharacterSimpleReadSchema]):
    async def __call__(self: Self, name: str) -> CharacterSimpleReadSchema:
        ...


class GetByNameCharacterUseCase(GetByNameCharacterUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, name: str) -> CharacterSimpleReadSchema:
        return await self.service.get_by_name(name)
