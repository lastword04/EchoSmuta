import uuid

import sqlalchemy as sa
from typing_extensions import Self

from ..models import HouseFurniture


class HouseFurnitureRepositoryProtocol:
    async def install(
        self: Self,
        house_id: uuid.UUID,
        inventory_item_id: uuid.UUID
    ) -> HouseFurniture:
        ...

    async def uninstall(
        self: Self,
        inventory_item_id: uuid.UUID
    ) -> bool:
        ...

    async def list_by_house(
        self: Self,
        house_id: uuid.UUID
    ) -> list[HouseFurniture]:
        ...

    async def get_by_inventory_item(
        self: Self,
        inventory_item_id: uuid.UUID
    ) -> HouseFurniture | None:
        ...

    async def get_all_inventory_item_ids(
        self: Self,
    ) -> list[uuid.UUID]:
        ...


class HouseFurnitureRepository(HouseFurnitureRepositoryProtocol):
    def __init__(self: Self, session):
        self.session = session

    async def install(
        self: Self,
        house_id: uuid.UUID,
        inventory_item_id: uuid.UUID
    ) -> HouseFurniture:
        async with self.session as session, session.begin():
            furniture = HouseFurniture(
                house_id=house_id,
                inventory_item_id=inventory_item_id,
            )
            session.add(furniture)
        return furniture

    async def uninstall(
        self: Self,
        inventory_item_id: uuid.UUID
    ) -> bool:
        async with self.session as session, session.begin():
            result = await session.execute(
                sa.delete(HouseFurniture).where(
                    HouseFurniture.inventory_item_id == inventory_item_id
                )
            )
            return result.rowcount > 0

    async def list_by_house(
        self: Self,
        house_id: uuid.UUID
    ) -> list[HouseFurniture]:
        async with self.session as session:
            stmt = (
                sa.select(HouseFurniture)
                .where(HouseFurniture.house_id == house_id)
                .order_by(HouseFurniture.created_at.asc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_inventory_item(
        self: Self,
        inventory_item_id: uuid.UUID
    ) -> HouseFurniture | None:
        async with self.session as session:
            stmt = (
                sa.select(HouseFurniture)
                .where(HouseFurniture.inventory_item_id == inventory_item_id)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()


    async def get_all_inventory_item_ids(
        self: Self,
    ) -> list[uuid.UUID]:
        async with self.session as session:
            stmt = sa.select(HouseFurniture.inventory_item_id)
            result = await session.execute(stmt)
            return [row.inventory_item_id for row in result.all()]