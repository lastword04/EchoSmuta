from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TavernMeal

ROTATION_SECONDS = 12 * 60 * 60


def current_period(now: datetime) -> int:
    """Номер текущего периода ротации, выровненного по epoch (UTC).

    Границы периодов — 00:00 и 12:00 UTC (03:00 и 15:00 по Москве).
    """
    return int(now.timestamp() // ROTATION_SECONDS)


def next_rotation_at(now: datetime) -> datetime:
    """Момент (UTC) границы следующего периода ротации."""
    next_period = (int(now.timestamp()) // ROTATION_SECONDS + 1) * ROTATION_SECONDS
    return datetime.fromtimestamp(next_period, tz=timezone.utc)


async def ensure_stock_rotation(session: AsyncSession) -> None:
    """Ленивая ротация стока: порции обновляются раз в период (12 часов).

    Обновляются только блюда, чей stock_period меньше текущего периода.
    """
    period = current_period(datetime.now(timezone.utc))
    await session.execute(
        update(TavernMeal)
        .where(TavernMeal.stock_period < period)
        .values(stock=TavernMeal.default_stock, stock_period=period)
    )
    await session.commit()
