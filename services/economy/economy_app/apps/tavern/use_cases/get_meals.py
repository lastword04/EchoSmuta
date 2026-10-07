from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..rotation import ensure_stock_rotation, next_rotation_at
from ..schemas import TavernMenuSchema
from ..models import TavernMeal


class GetMealsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __call__(self) -> TavernMenuSchema:
        await ensure_stock_rotation(self.session)
        result = await self.session.scalars(
            select(TavernMeal)
            .where(TavernMeal.is_active.is_(True))
            .order_by(TavernMeal.order.asc())
        )
        meals = list(result.all())
        return TavernMenuSchema(
            meals=meals,
            next_rotation_at=next_rotation_at(datetime.now(timezone.utc)),
        )
