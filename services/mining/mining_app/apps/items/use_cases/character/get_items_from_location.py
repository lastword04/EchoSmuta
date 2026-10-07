from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from .....core.utils.exceptions import PermissionDeniedError
from ...schemas import LocationItemsGroupedSchema
from ...services.character.character_items import CharacterItemServiceProtocol


class GetItemsFromLocationUseCaseProtocol(UseCaseProtocol[LocationItemsGroupedSchema]):
    async def __call__(self: Self, token: UserTokenDataReadSchema) -> LocationItemsGroupedSchema:
        ...


class GetItemsFromLocationUseCase(GetItemsFromLocationUseCaseProtocol):
    def __init__(self: Self, service: CharacterItemServiceProtocol):
        self.service = service

    async def __call__(self: Self, token: UserTokenDataReadSchema) -> LocationItemsGroupedSchema:
        if not token.character_id:
            raise PermissionDeniedError()
        
        return await self.service.get_items_from_location(token.character_id)
