from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.characters import CharacterOnlineStatus
from shared.exceptions import CharacterIsNotOnlineError
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import GetIsOnlineCharacterServiceProtocol 

class GetIsOnlineCharacterOrRaiseUseCaseProtocol(UseCaseProtocol[CharacterOnlineStatus]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterOnlineStatus:
        ...


class GetIsOnlineCharacterOrRaiseUseCase(GetIsOnlineCharacterOrRaiseUseCaseProtocol):
    def __init__(self: Self, service: GetIsOnlineCharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterOnlineStatus:
        if not token.character_id:
            raise CharacterIsNotOnlineError()
        status = await self.service.get_is_online(token.character_id)
        if not status.is_online:
            raise CharacterIsNotOnlineError(token.character_id)
