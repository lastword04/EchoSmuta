import uuid
from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 


class DeleteCharacterUseCaseProtocol(UseCaseProtocol[None]):
    async def __call__(self: Self, character_id: uuid.UUID) -> None:
        ...


class DeleteCharacterUseCase(DeleteCharacterUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, character_id: uuid.UUID) -> None:
        await self.service.delete(character_id)
