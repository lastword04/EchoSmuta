import uuid
from typing import Self

from .....core.use_cases import UseCaseProtocol
from ...schemas import ItemDetailsSchema
from ...services.items.items import ItemServiceProtocol


class GetItemDetailsUseCaseProtocol(UseCaseProtocol[ItemDetailsSchema]):
    async def __call__(self: Self, item_id: uuid.UUID) -> ItemDetailsSchema:
        ...


class GetItemDetailsUseCase(GetItemDetailsUseCaseProtocol):
    def __init__(self: Self, service: ItemServiceProtocol):
        self.service = service

    async def __call__(self: Self, item_id: uuid.UUID) -> ItemDetailsSchema:
        return await self.service.get_item_details(item_id)
