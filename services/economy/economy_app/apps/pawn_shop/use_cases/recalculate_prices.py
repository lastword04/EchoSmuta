import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....settings import settings
from ..models import (
    CurrentPrice,
    PoolSnapshot,
    PoolType,
    PriceRecalculation,
    PriceRecalculationItem,
    PriceRecalculationReason,
    PriceRecalculationStatus,
    Resource,
    ResourceSourceType,
)
from ..services.pool_collector import PoolCollectorService


BUYOUT_WEIGHT = Decimal("0.5")
LOCATIONS_WEIGHT = Decimal("0.3")
PLAYERS_WEIGHT = Decimal("0.2")
MAX_PRICE_CHANGE_PERCENT = Decimal("30")


class RecalculatePricesUseCase:
    def __init__(self, pool_collector: PoolCollectorService) -> None:
        self.pool_collector = pool_collector

    async def __call__(
        self,
        session: AsyncSession,
        reason: PriceRecalculationReason = PriceRecalculationReason.SCHEDULED,
    ) -> PriceRecalculation:
        now = datetime.now(timezone.utc)
        next_run_at = self._next_recalculation_time(now)
        recalculation = PriceRecalculation(started_at=now, status=PriceRecalculationStatus.STARTED, reason=reason)
        session.add(recalculation)
        await session.flush()

        try:
            resources = list((await session.scalars(
                select(Resource).where(
                    Resource.source_type == ResourceSourceType.RESOURCE_LOCATION,
                    Resource.is_tradeable.is_(True),
                )
            )).all())
            buyout_quantities = await self.pool_collector.get_buyout_quantities(session)
            location_quantities = await self.pool_collector.get_location_quantities(resources)
            player_quantities = await self.pool_collector.get_player_quantities()

            for resource in resources:
                await self._recalculate_resource(
                    session=session,
                    recalculation_id=recalculation.id,
                    resource=resource,
                    current_buyout=buyout_quantities.get(resource.id, Decimal("0")),
                    current_locations=location_quantities.get(resource.code, Decimal("0")),
                    current_players=player_quantities.get(resource.code, Decimal("0")),
                    now=now,
                    next_run_at=next_run_at,
                )

            recalculation.status = PriceRecalculationStatus.COMPLETED
            recalculation.finished_at = datetime.now(timezone.utc)
            recalculation.next_recalculation_at = next_run_at
            await session.commit()
            await session.refresh(recalculation)
            return recalculation
        except httpx.HTTPError as exc:
            await session.rollback()
            return await self._record_failure(session, reason, str(exc), now)
        except Exception as exc:
            await session.rollback()
            return await self._record_failure(session, reason, str(exc), now)

    async def _recalculate_resource(
        self,
        session: AsyncSession,
        recalculation_id: uuid.UUID,
        resource: Resource,
        current_buyout: Decimal,
        current_locations: Decimal,
        current_players: Decimal,
        now: datetime,
        next_run_at: datetime,
    ) -> None:
        price = await session.scalar(select(CurrentPrice).where(CurrentPrice.resource_id == resource.id).with_for_update())
        if price is None:
            price = CurrentPrice(
                resource_id=resource.id,
                sell_price=resource.base_sell_price,
                buy_price=resource.base_buy_price,
            )
            session.add(price)
            await session.flush()

        previous = {
            PoolType.BUYOUT: await self._previous_quantity(session, resource.id, PoolType.BUYOUT),
            PoolType.LOCATIONS: await self._previous_quantity(session, resource.id, PoolType.LOCATIONS),
            PoolType.PLAYERS: await self._previous_quantity(session, resource.id, PoolType.PLAYERS),
        }
        current = {
            PoolType.BUYOUT: current_buyout,
            PoolType.LOCATIONS: current_locations,
            PoolType.PLAYERS: current_players,
        }

        buyout_delta = self._percentage_delta(previous[PoolType.BUYOUT], current[PoolType.BUYOUT])
        locations_delta = self._percentage_delta(previous[PoolType.LOCATIONS], current[PoolType.LOCATIONS])
        players_delta = self._percentage_delta(previous[PoolType.PLAYERS], current[PoolType.PLAYERS])
        weighted_delta = (buyout_delta * BUYOUT_WEIGHT + locations_delta * LOCATIONS_WEIGHT + players_delta * PLAYERS_WEIGHT) / Decimal("2")
        price_delta = self._clamp(-weighted_delta, -MAX_PRICE_CHANGE_PERCENT, MAX_PRICE_CHANGE_PERCENT)
        multiplier = Decimal("1") + price_delta / Decimal("100")

        old_sell = Decimal(str(price.sell_price))
        old_buy = Decimal(str(price.buy_price))

        new_sell = (old_sell * multiplier).quantize(Decimal("0.0001"))
        new_buy = (old_buy * multiplier).quantize(Decimal("0.0001"))
        if resource.min_sell_price is not None:
            new_sell = max(Decimal(str(resource.min_sell_price)), new_sell)
        if resource.max_sell_price is not None:
            new_sell = min(Decimal(str(resource.max_sell_price)), new_sell)
        if resource.min_buy_price is not None:
            new_buy = max(Decimal(str(resource.min_buy_price)), new_buy)
        if resource.max_buy_price is not None:
            new_buy = min(Decimal(str(resource.max_buy_price)), new_buy)

        price.previous_sell_price = old_sell
        price.previous_buy_price = old_buy
        price.sell_price = new_sell
        price.buy_price = new_buy
        price.last_recalculated_at = now
        price.next_recalculation_at = next_run_at

        for pool_type, quantity in current.items():
            session.add(PoolSnapshot(
                resource_id=resource.id,
                recalculation_id=recalculation_id,
                pool_type=pool_type,
                quantity=quantity,
                snapshot_at=now,
            ))

        session.add(PriceRecalculationItem(
            recalculation_id=recalculation_id,
            resource_id=resource.id,
            old_price=old_sell,   
            new_price=new_sell,
            buyout_previous_quantity=previous[PoolType.BUYOUT],
            buyout_current_quantity=current[PoolType.BUYOUT],
            locations_previous_quantity=previous[PoolType.LOCATIONS],
            locations_current_quantity=current[PoolType.LOCATIONS],
            players_previous_quantity=previous[PoolType.PLAYERS],
            players_current_quantity=current[PoolType.PLAYERS],
            buyout_delta_percent=buyout_delta,
            locations_delta_percent=locations_delta,
            players_delta_percent=players_delta,
            price_delta_percent=price_delta,
        ))

    async def _previous_quantity(self, session: AsyncSession, resource_id: uuid.UUID, pool_type: PoolType) -> Decimal:
        snapshot = await session.scalar(
            select(PoolSnapshot)
            .where(PoolSnapshot.resource_id == resource_id, PoolSnapshot.pool_type == pool_type)
            .order_by(PoolSnapshot.snapshot_at.desc())
            .limit(1)
        )
        return Decimal(str(snapshot.quantity)) if snapshot is not None else Decimal("0")

    async def _record_failure(
        self,
        session: AsyncSession,
        reason: PriceRecalculationReason,
        error_message: str,
        started_at: datetime,
    ) -> PriceRecalculation:
        recalculation = PriceRecalculation(
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            status=PriceRecalculationStatus.FAILED,
            reason=reason,
            next_recalculation_at=datetime.now(timezone.utc) + timedelta(minutes=settings.pricing.recalculation_retry_minutes),
            error_message=error_message[:2000],
        )
        session.add(recalculation)
        await session.commit()
        await session.refresh(recalculation)
        return recalculation

    @staticmethod
    def _percentage_delta(previous: Decimal, current: Decimal) -> Decimal:
        if previous == 0:
            return Decimal("0")
        return ((current - previous) / previous * Decimal("100")).quantize(Decimal("0.0001"))

    @staticmethod
    def _clamp(value: Decimal, min_value: Decimal, max_value: Decimal) -> Decimal:
        return max(min_value, min(max_value, value)).quantize(Decimal("0.0001"))

    @staticmethod
    def _next_recalculation_time(now: datetime) -> datetime:
        hours = random.uniform(settings.pricing.recalculation_min_hours, settings.pricing.recalculation_max_hours)
        return now + timedelta(hours=hours)
