import uuid
from typing_extensions import Self
from shared.schemas.auth import UserTokenDataReadSchema
from .....core.use_cases import UseCaseProtocol 
from ...services.character.characters import CharacterAttachmentServiceProtocol 


class DetachCharacterUseCaseProtocol(UseCaseProtocol[bool]):
    async def __call__(self: Self, token: UserTokenDataReadSchema, character_id: uuid.UUID) -> bool:
        ...


class DetachCharacterUseCase(DetachCharacterUseCaseProtocol):
    def __init__(self: Self, service: CharacterAttachmentServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema, character_id: uuid.UUID) -> bool:
        return await self.service.detach(token.user_id, character_id)
