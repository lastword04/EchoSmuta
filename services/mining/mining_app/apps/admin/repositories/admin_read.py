import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...items.models import (
    CharacterEquipment,
    CityTradingShop,
    InventoryItem,
    Item,
    SaleInventoryItem,
)
from ...resources.models import CharacterResource, Resource


def _ilike_pattern(search: str) -> str:
    escaped_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped_search}%"


class AdminReadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_items(self, item_type: str | None, location_slug: str | None, search: str | None, limit: int, offset: int):
        filters = []
        if item_type:
            filters.append(Item.item_type == item_type)
        if location_slug:
            filters.append(Item.location_slug == location_slug)
        if search:
            pattern = _ilike_pattern(search)
            filters.append(sa.or_(Item.name.ilike(pattern, escape="\\"), Item.slug.ilike(pattern, escape="\\")))
        statement = sa.select(Item).where(*filters).order_by(Item.name).offset(offset).limit(limit)
        count_statement = sa.select(sa.func.count()).select_from(Item).where(*filters)
        async with self.session as session:
            return (await session.scalars(statement)).all(), (await session.scalar(count_statement) or 0)

    async def list_resources(self, category: str | None, search: str | None, limit: int, offset: int):
        filters = []
        if category:
            filters.append(Resource.category == category)
        if search:
            pattern = _ilike_pattern(search)
            filters.append(sa.or_(Resource.name.ilike(pattern, escape="\\"), Resource.slug.ilike(pattern, escape="\\")))
        statement = sa.select(Resource).where(*filters).order_by(Resource.name).offset(offset).limit(limit)
        count_statement = sa.select(sa.func.count()).select_from(Resource).where(*filters)
        async with self.session as session:
            return (await session.scalars(statement)).all(), (await session.scalar(count_statement) or 0)

    async def get_resource_categories(self) -> list[str]:
        statement = sa.select(Resource.category).where(Resource.category.is_not(None)).distinct().order_by(Resource.category)
        async with self.session as session:
            return list((await session.scalars(statement)).all())

    async def get_character_resources(self, character_id: uuid.UUID):
        statement = (
            sa.select(CharacterResource, Resource)
            .join(Resource, CharacterResource.resource_slug == Resource.slug)
            .where(CharacterResource.character_id == character_id)
            .order_by(Resource.name)
        )
        async with self.session as session:
            return (await session.execute(statement)).all()

    async def get_character_inventory(self, character_id: uuid.UUID):
        statement = (
            sa.select(InventoryItem, SaleInventoryItem.price, CharacterEquipment.id)
            .outerjoin(CityTradingShop, InventoryItem.shop_id == CityTradingShop.id)
            .outerjoin(SaleInventoryItem, SaleInventoryItem.inventory_item_id == InventoryItem.id)
            .outerjoin(CharacterEquipment, CharacterEquipment.inventory_item_id == InventoryItem.id)
            .options(joinedload(InventoryItem.item))
            .where(sa.or_(InventoryItem.character_id == character_id, CityTradingShop.character_id == character_id))
            .order_by(InventoryItem.created_at.desc())
        )
        async with self.session as session:
            return (await session.execute(statement)).all()
