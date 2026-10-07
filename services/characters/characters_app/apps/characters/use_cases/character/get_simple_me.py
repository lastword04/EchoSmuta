from typing_extensions import Self
from shared.schemas.characters import CharacterReadSchema
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 


class GetSimpleMeCharactersUseCaseProtocol(UseCaseProtocol[CharacterReadSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterReadSchema:
        ...


class GetSimpleMeCharactersUseCase(GetSimpleMeCharactersUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> CharacterReadSchema:
        return await self.service.get_simple_by_user_id(token.user_id)
