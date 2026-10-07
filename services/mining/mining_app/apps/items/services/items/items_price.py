from typing import Protocol

from ...repositories.items.items_price import ItemPriceRepositoryProtocol
from ...schemas import ItemPriceCreateSchema, ItemPriceReadSchema


class ItemPriceServiceProtocol(Protocol):
    async def get_all(self) -> list[ItemPriceReadSchema]:
        ...

    async def bulk_create(self, items: list[ItemPriceCreateSchema]) -> list[ItemPriceReadSchema]:
        ...

class ItemPriceService(ItemPriceServiceProtocol):
    def __init__(self, repository: ItemPriceRepositoryProtocol):
        self.repository = repository

    async def get_all(self) -> list[ItemPriceReadSchema]:
        return await self.repository.get_all()
    
    async def bulk_create(self, items: list[ItemPriceCreateSchema]) -> list[ItemPriceReadSchema]:
        return await self.repository.bulk_create(items)