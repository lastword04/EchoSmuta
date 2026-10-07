import uuid
from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from ...schemas import LocationItemsGroupedSchema
from ...services.sale.sale_items import SaleItemServiceProtocol


class RemoveItemFromSaleUseCaseProtocol(UseCaseProtocol[LocationItemsGroupedSchema]):
    async def __call__(
        self: Self,
        inventory_item_id: uuid.UUID,
        user: UserTokenDataReadSchema,
        amount: int | None = None
    ) -> LocationItemsGroupedSchema:
        ...


class RemoveItemFromSaleUseCase(RemoveItemFromSaleUseCaseProtocol):
    def __init__(self: Self, service: SaleItemServiceProtocol):
        self.service = service

    async def __call__(
        self: Self,
        inventory_item_id: uuid.UUID,
        user: UserTokenDataReadSchema,
        amount: int | None = None
    ) -> LocationItemsGroupedSchema:
        return await self.service.remove_item_from_sale(
            character_id=user.character_id,
            inventory_item_id=inventory_item_id,
            amount=amount
        )