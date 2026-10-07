import uuid
from typing import Sequence
from typing_extensions import Self
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 
from shared.schemas.characters import CharacterSimpleListReadSchema


class GetSimpleByIdsCharactersUseCaseProtocol(UseCaseProtocol[CharacterSimpleListReadSchema]):
    async def __call__(self: Self, ids: Sequence[uuid.UUID]) -> CharacterSimpleListReadSchema:
        ...


class GetSimpleByIdsCharactersUseCase(GetSimpleByIdsCharactersUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self,  ids: Sequence[uuid.UUID]) -> CharacterSimpleListReadSchema:
        return await self.service.get_simple_by_ids(ids)
