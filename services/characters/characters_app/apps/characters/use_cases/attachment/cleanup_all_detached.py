from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterCleanupServiceProtocol 


class CleanupDetachedCharactersUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self) -> bool:
        ...


class CleanupDetachedCharactersUseCase(CleanupDetachedCharactersUseCaseProtocol):
    def __init__(self: Self, service: CharacterCleanupServiceProtocol):
        self.service = service

    async def __call__(self: Self) -> bool:
        return await self.service.delete_all_detached_characters()
