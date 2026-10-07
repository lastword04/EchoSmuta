import uuid
from typing import Protocol

from ...repositories.items.items import ItemRepositoryProtocol
from ...repositories.items.items_component import ItemComponentRepositoryProtocol
from ...schemas import ItemCreateSchema, ItemDetailsSchema, ItemReadSchema


class ItemServiceProtocol(Protocol):
    async def get_all(self) -> list[ItemReadSchema]:
        ...

    async def bulk_create(self, items: list[ItemCreateSchema]) -> list[ItemReadSchema]:
        ...

    async def bulk_update(self, items: list[ItemCreateSchema]) -> list[ItemReadSchema]:
        ...

    async def get_by_slug(self, slug: str) -> ItemReadSchema:
        ...

    async def get_item_details(self, item_id: uuid.UUID) -> ItemDetailsSchema:
        ...

class ItemService(ItemServiceProtocol):
    def __init__(self, repository: ItemRepositoryProtocol, component_repository: ItemComponentRepositoryProtocol):
        self.repository = repository
        self.component_repository = component_repository

    async def get_all(self) -> list[ItemReadSchema]:
        return await self.repository.get_all()
    
    async def bulk_create(self, items: list[ItemCreateSchema]) -> list[ItemReadSchema]:
        return await self.repository.bulk_create(items)

    async def bulk_update(self, items: list[ItemCreateSchema]) -> list[ItemReadSchema]:
        return await self.repository.bulk_update(items)

    async def get_by_slug(self, slug: str) -> ItemReadSchema:
        return await self.repository.get_by_slug(slug)

    async def get_item_details(self, item_id: uuid.UUID) -> ItemDetailsSchema:
        """Получить детальную информацию об Item с компонентами"""
        item = await self.repository.get(item_id)
        components = await self.component_repository.get_components_with_resource_names(item.slug)
        
        return ItemDetailsSchema(
            item=item,
            components=components
        )