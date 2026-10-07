from sqlalchemy import select

from .....core.repositories.base_repository import BaseRepositoryImpl
from ....resources.models import Resource
from ...models import ItemComponent
from ...schemas import (
    ItemComponentCreateSchema,
    ItemComponentReadSchema,
    ItemComponentUpdateSchema,
    ItemComponentWithResourceSchema,
)


class ItemComponentRepositoryProtocol(
    BaseRepositoryImpl[
        ItemComponent,
        ItemComponentReadSchema,
        ItemComponentCreateSchema,
        ItemComponentUpdateSchema
    ]
):
    async def get_components_with_resource_names(self, item_slug: str) -> list[ItemComponentWithResourceSchema]:
        ...

class ItemComponentRepository(ItemComponentRepositoryProtocol):
    async def get_components_with_resource_names(self, item_slug: str) -> list[ItemComponentWithResourceSchema]:
        """Получить компоненты с названиями ресурсов"""
        stmt = (
            select(
                ItemComponent.id,
                ItemComponent.item_slug,
                ItemComponent.resource_slug,
                ItemComponent.quantity,
                Resource.name.label('resource_name')
            )
            .join(Resource, ItemComponent.resource_slug == Resource.slug)
            .where(ItemComponent.item_slug == item_slug)
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        return [
            ItemComponentWithResourceSchema(
                id=row.id,
                item_slug=row.item_slug,
                resource_slug=row.resource_slug,
                quantity=row.quantity,
                resource_name=row.resource_name
            )
            for row in rows
        ]