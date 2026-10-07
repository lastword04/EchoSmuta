import uuid
from decimal import Decimal
from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema

from .....core.use_cases import UseCaseProtocol
from ...schemas import LocationItemsGroupedSchema
from ...services.sale.sale_items import SaleItemServiceProtocol


class UpdateSalePriceUseCaseProtocol(UseCaseProtocol[LocationItemsGroupedSchema]):
    async def __call__(
        self: Self,
        inventory_item_id: uuid.UUID,
        price: Decimal,
        user: UserTokenDataReadSchema
    ) -> LocationItemsGroupedSchema:
        ...


class UpdateSalePriceUseCase(UpdateSalePriceUseCaseProtocol):
    def __init__(self: Self, service: SaleItemServiceProtocol):
        self.service = service

    async def __call__(
        self: Self,
        inventory_item_id: uuid.UUID,
        price: Decimal,
        user: UserTokenDataReadSchema
    ) -> LocationItemsGroupedSchema:
        return await self.service.update_sale_price(
            character_id=user.character_id,
            inventory_item_id=inventory_item_id,
            price=price
        )