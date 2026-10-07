from typing import Protocol

from ...repositories.items.items_component import ItemComponentRepositoryProtocol
from ...schemas import (
    ItemComponentCreateSchema,
    ItemComponentReadSchema,
    ItemComponentWithResourceSchema,
)


class ItemComponentServiceProtocol(Protocol):
    async def get_all(self) -> list[ItemComponentReadSchema]:
        ...

    async def bulk_create(self, items: list[ItemComponentCreateSchema]) -> list[ItemComponentReadSchema]:
        ...

    async def get_components_with_resource_names(self, item_slug: str) -> list[ItemComponentWithResourceSchema]:
        ...

class ItemComponentService(ItemComponentServiceProtocol):
    def __init__(self, repository: ItemComponentRepositoryProtocol):
        self.repository = repository

    async def get_all(self) -> list[ItemComponentReadSchema]:
        return await self.repository.get_all()
    
    async def bulk_create(self, items: list[ItemComponentCreateSchema]) -> list[ItemComponentReadSchema]:
        return await self.repository.bulk_create(items)

    async def get_components_with_resource_names(self, item_slug: str) -> list[ItemComponentWithResourceSchema]:
        return await self.repository.get_components_with_resource_names(item_slug)