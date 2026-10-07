import uuid
from typing_extensions import Self
from shared.schemas.characters import CharacterOnlineStatus
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import GetIsOnlineCharacterServiceProtocol 

class GetIsOnlineCharacterUseCaseProtocol(UseCaseProtocol[CharacterOnlineStatus]):
    async def __call__(self: Self, id: uuid.UUID) -> CharacterOnlineStatus:
        ...


class GetIsOnlineCharacterUseCase(GetIsOnlineCharacterUseCaseProtocol):
    def __init__(self: Self, service: GetIsOnlineCharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, id: uuid.UUID) -> CharacterOnlineStatus:
        return await self.service.get_is_online(id)
