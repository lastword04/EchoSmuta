from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.characters import CharacterReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterAttachmentServiceProtocol 


class GetDetachCharacterStatusUseCaseProtocol(UseCaseProtocol[list[CharacterReadSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterReadSchema]:
        ...


class GetDetachCharacterStatusUseCase(GetDetachCharacterStatusUseCaseProtocol):
    def __init__(self: Self, service: CharacterAttachmentServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[CharacterReadSchema]:
        return await self.service.get_detached_characters(token.user_id)
