import uuid
from typing import Protocol
from typing_extensions import Self
from sqlalchemy.dialects.postgresql import insert
import sqlalchemy as sa
from ....core.db import AsyncSession
from ..models import InventoryItemWorkAccumulator


class InventoryItemWorkAccumulatorRepositoryProtocol:
    async def add_work_minutes(self: Self, inventory_item_id: uuid.UUID, minutes: float) -> None: ...
    async def get_accumulated(self: Self, inventory_item_id: uuid.UUID) -> float: ...
    async def subtract_work_minutes(self: Self, inventory_item_id: uuid.UUID, minutes: float) -> float: ...


class InventoryItemWorkAccumulatorRepository(InventoryItemWorkAccumulatorRepositoryProtocol):
    def __init__(self: Self, session: AsyncSession):
        self.session = session

    async def add_work_minutes(self: Self, inventory_item_id: uuid.UUID, minutes: float) -> None:
        """Добавить минуты работы. Если записи нет — создать с minutes."""
        stmt = (
            insert(InventoryItemWorkAccumulator)
            .values(inventory_item_id=inventory_item_id, work_minutes=minutes)
            .on_conflict_do_update(
                index_elements=['inventory_item_id'],
                set_={'work_minutes': InventoryItemWorkAccumulator.work_minutes + minutes}
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_accumulated(self: Self, inventory_item_id: uuid.UUID) -> float:
        """Получить накопленные минуты."""
        result = await self.session.execute(
            sa.select(InventoryItemWorkAccumulator.work_minutes)
            .where(InventoryItemWorkAccumulator.inventory_item_id == inventory_item_id)
        )
        row = result.scalar_one_or_none()
        return row if row is not None else 0.0

    async def subtract_work_minutes(self: Self, inventory_item_id: uuid.UUID, minutes: float) -> float:
        """Вычесть минуты и вернуть остаток."""
        result = await self.session.execute(
            sa.update(InventoryItemWorkAccumulator)
            .where(InventoryItemWorkAccumulator.inventory_item_id == inventory_item_id)
            .values(work_minutes=InventoryItemWorkAccumulator.work_minutes - minutes)
            .returning(InventoryItemWorkAccumulator.work_minutes)
        )
        await self.session.commit()
        row = result.scalar_one_or_none()
        return row if row is not None else 0.0