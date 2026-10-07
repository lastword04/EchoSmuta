import uuid
from typing import Self

from shared.schemas.auth import UserTokenDataReadSchema
from shared.schemas.base import StatusOkSchema

from .....core.use_cases import UseCaseProtocol
from ...services.purchase.purchase_items import PurchaseItemServiceProtocol


class PurchaseItemUseCaseProtocol(UseCaseProtocol[StatusOkSchema]):
    async def __call__(
        self: Self,
        inventory_item_id: uuid.UUID,
        user: UserTokenDataReadSchema,
        amount: int | None = None
    ) -> StatusOkSchema:
        ...


class PurchaseItemUseCase(PurchaseItemUseCaseProtocol):
    def __init__(self: Self, service: PurchaseItemServiceProtocol):
        self.service = service

    async def __call__(
        self: Self,
        inventory_item_id: uuid.UUID,
        user: UserTokenDataReadSchema,
        amount: int | None = None
    ) -> StatusOkSchema:
        return await self.service.purchase_item(
            inventory_item_id=inventory_item_id,
            buyer_character_id=user.character_id,
            amount=amount,
        )