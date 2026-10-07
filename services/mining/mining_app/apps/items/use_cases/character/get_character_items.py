from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import InventoryItemReadSchema
from ...services.character.character_items import CharacterItemServiceProtocol


class GetCharacterItemsUseCaseProtocol(UseCaseProtocol[list[InventoryItemReadSchema]]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[InventoryItemReadSchema]:
        ...


class GetCharacterItemsUseCase(GetCharacterItemsUseCaseProtocol):
    def __init__(self: Self, service: CharacterItemServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> list[InventoryItemReadSchema]:
        if not token.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_character_items(token.character_id)
