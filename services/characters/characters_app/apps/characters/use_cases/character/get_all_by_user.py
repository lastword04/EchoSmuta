from typing_extensions import Self
from shared.schemas.characters import CharacterReadSchema
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterServiceProtocol 


class GetCharactersByUserUseCaseProtocol(UseCaseProtocol[list[CharacterReadSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterReadSchema]:
        ...


class GetCharactersByUserUseCase(GetCharactersByUserUseCaseProtocol):
    def __init__(self: Self, service: CharacterServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterReadSchema]:
        return await self.service.get_all_by_user(token.user_id)
