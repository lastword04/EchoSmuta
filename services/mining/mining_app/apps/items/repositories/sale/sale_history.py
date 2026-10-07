import uuid
from decimal import Decimal
from typing import Protocol

import sqlalchemy as sa

from .....core.db import AsyncSession
from ...models import SaleHistory


class SaleHistoryRepositoryProtocol(Protocol):
    async def create(
        self,
        shop_id: uuid.UUID | None,
        seller_character_id: uuid.UUID,
        buyer_character_id: uuid.UUID,
        buyer_name: str,
        item_slug: str,
        item_name: str,
        amount: int,
        price: Decimal,
        tax: Decimal,
        location_slug: str,
    ) -> SaleHistory: ...

    async def list_by_seller(self, seller_character_id: uuid.UUID, limit: int = 30, location_slug: str | None = None) -> list[SaleHistory]: ...
 

class SaleHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        shop_id: uuid.UUID | None,
        seller_character_id: uuid.UUID,
        buyer_character_id: uuid.UUID,
        buyer_name: str,
        item_slug: str,
        item_name: str,
        amount: int,
        price: Decimal,
        tax: Decimal,
        location_slug: str,
    ) -> SaleHistory:
        row = SaleHistory(
            shop_id=shop_id,
            seller_character_id=seller_character_id,
            buyer_character_id=buyer_character_id,
            buyer_name=buyer_name,
            item_slug=item_slug,
            item_name=item_name,
            amount=amount,
            price=price,
            tax=tax,
            location_slug=location_slug,
        )
        self.session.add(row)
        await self.session.commit()
        return row

    async def list_by_seller(self, seller_character_id: uuid.UUID, limit: int = 30, location_slug: str | None = None) -> list[SaleHistory]:
        stmt = sa.select(SaleHistory).where(SaleHistory.seller_character_id == seller_character_id)
        if location_slug:
            stmt = stmt.where(SaleHistory.location_slug == location_slug)
        stmt = stmt.order_by(SaleHistory.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())