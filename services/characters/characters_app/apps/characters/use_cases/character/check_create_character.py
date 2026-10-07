from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...schemas import CharacterCreationStatus
from ...services.character.characters import CharacterCreateCheckerProtocol 


class CheckCreateCharacterStatusUseCaseProtocol(UseCaseProtocol[CharacterCreationStatus]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterCreationStatus:
        ...


class CheckCreateCharacterStatusUseCase(CheckCreateCharacterStatusUseCaseProtocol):
    def __init__(self: Self, service: CharacterCreateCheckerProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterCreationStatus:
        return await self.service.check_on_limit_characters(token.user_id)
