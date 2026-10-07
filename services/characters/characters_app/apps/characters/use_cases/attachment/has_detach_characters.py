from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterAttachmentServiceProtocol 


class HasDetachCharacterStatusUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> bool:
        ...


class HasDetachCharacterStatusUseCase(HasDetachCharacterStatusUseCaseProtocol):
    def __init__(self: Self, service: CharacterAttachmentServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> bool:
        return await self.service.has_detached_characters(token.user_id)
