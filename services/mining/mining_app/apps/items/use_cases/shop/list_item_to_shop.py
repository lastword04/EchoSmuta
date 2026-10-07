import uuid
from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from ...schemas import LocationItemsGroupedSchema
from ...services.shop.shop_items import ShopItemServiceProtocol


class ListItemToShopUseCaseProtocol(UseCaseProtocol[LocationItemsGroupedSchema]):
    async def __call__(
        self: Self,
        item_id: uuid.UUID,
        user: UserTokenDataReadSchema,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        ...


class ListItemToShopUseCase(ListItemToShopUseCaseProtocol):
    def __init__(self: Self, service: ShopItemServiceProtocol):
        self.service = service

    async def __call__(
        self: Self,
        item_id: uuid.UUID,
        user: UserTokenDataReadSchema,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        return await self.service.list_item_to_shop(
            character_id=user.character_id,
            item_id=item_id,
            amount=amount
        )