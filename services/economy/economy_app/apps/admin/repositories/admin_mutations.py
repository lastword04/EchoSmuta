import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...pawn_shop.models import BuyoutStock, EconomyTransaction, Resource, TransactionType


class AdminMutationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_stock_for_update(self, resource_id: uuid.UUID) -> BuyoutStock | None:
        return await self.session.scalar(
            select(BuyoutStock).where(BuyoutStock.resource_id == resource_id).with_for_update()
        )

    async def create_stock(self, resource_id: uuid.UUID, quantity: int) -> BuyoutStock:
        stock = BuyoutStock(resource_id=resource_id, quantity=quantity)
        self.session.add(stock)
        return stock

    async def get_resource_for_update(self, resource_id: uuid.UUID) -> Resource | None:
        return await self.session.scalar(
            select(Resource).where(Resource.id == resource_id).with_for_update()
        )

    def log_admin_action(self, resource_id: uuid.UUID, quantity: int, price_per_unit: Decimal) -> None:
        self.session.add(EconomyTransaction(
            transaction_type=TransactionType.ADMIN_RESET,
            resource_id=resource_id,
            quantity=quantity,
            price_per_unit=price_per_unit,
            total=Decimal("0"),
            buyer_id=None,
            seller_id=None,
            lot_id=None,
        ))