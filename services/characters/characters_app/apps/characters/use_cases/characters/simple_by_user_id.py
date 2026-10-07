import uuid
from typing_extensions import Self
from shared.schemas.characters import CharacterSimpleReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 


class GetSimpleCharacterByUserUseCaseProtocol(UseCaseProtocol[CharacterSimpleReadSchema]):
    async def __call__(self: Self, user_id: uuid.UUID) -> CharacterSimpleReadSchema:
        ...


class GetSimpleCharacterByUserUseCase(GetSimpleCharacterByUserUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, user_id: uuid.UUID) -> CharacterSimpleReadSchema:
        return await self.service.get_simple_by_user_id(user_id)
