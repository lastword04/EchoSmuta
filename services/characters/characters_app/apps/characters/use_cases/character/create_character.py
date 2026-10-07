from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from shared.schemas.characters import CharacterCreateSchema, CharacterReadSchema
from ...services.character.characters import CharacterServiceProtocol 


class CreateCharacterUseCaseProtocol(UseCaseProtocol[CharacterReadSchema]):
    async def __call__(self: Self, data: CharacterCreateSchema) -> CharacterReadSchema:
        ...


class CreateCharacterUseCase(CreateCharacterUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, data: CharacterCreateSchema) -> CharacterReadSchema:
        return await self.service.create_default(data)
