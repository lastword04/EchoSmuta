import uuid
from decimal import Decimal
from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from ...schemas import LocationItemsGroupedSchema
from ...services.sale.sale_items import SaleItemServiceProtocol


class AddItemToSaleUseCaseProtocol(UseCaseProtocol[LocationItemsGroupedSchema]):
    async def __call__(
        self: Self,
        inventory_item_id: uuid.UUID,
        price: Decimal,
        user: UserTokenDataReadSchema,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        ...


class AddItemToSaleUseCase(AddItemToSaleUseCaseProtocol):
    def __init__(self: Self, service: SaleItemServiceProtocol):
        self.service = service

    async def __call__(
        self: Self,
        inventory_item_id: uuid.UUID,
        price: Decimal,
        user: UserTokenDataReadSchema,
        amount: int = 1
    ) -> LocationItemsGroupedSchema:
        return await self.service.add_item_to_sale(
            character_id=user.character_id,
            inventory_item_id=inventory_item_id,
            price=price,
            amount=amount
        )