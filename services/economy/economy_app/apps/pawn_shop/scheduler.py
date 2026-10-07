import asyncio
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

from sqlalchemy import select

from ...core.clients.depends import get_mining_client
from ...core.db import AsyncSessionFactory
from ...settings import settings
from .models import EconomySchedulerState, PriceRecalculation, PriceRecalculationReason, PriceRecalculationStatus
from .depends import get_economy_events
from .services.pool_collector import PoolCollectorService
from .use_cases.recalculate_prices import RecalculatePricesUseCase

PRICE_RECALCULATION_JOB = "price_recalculation"


async def start_pricing_scheduler(stop_event: asyncio.Event) -> None:
    if not settings.pricing.scheduler_enabled:
        return
    while not stop_event.is_set():
        try:
            await run_scheduled_price_recalculation()
        except Exception:
            # Ошибки конкретного тика не должны убивать фоновый цикл,
            # но они обязаны быть видны в логах.
            logger.exception("Pricing scheduler tick failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.pricing.scheduler_check_interval_seconds)
        except asyncio.TimeoutError:
            continue


async def run_scheduled_price_recalculation(force: bool = False) -> PriceRecalculation | None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionFactory() as session:
        state = await session.scalar(
            select(EconomySchedulerState)
            .where(EconomySchedulerState.job_name == PRICE_RECALCULATION_JOB)
            .with_for_update()
        )
        if state is None:
            state = EconomySchedulerState(job_name=PRICE_RECALCULATION_JOB, next_run_at=now)
            session.add(state)
            await session.flush()

        if not force and state.next_run_at > now:
            await session.rollback()
            return None
        if state.locked_until is not None and state.locked_until > now:
            await session.rollback()
            return None

        state.locked_until = now + timedelta(minutes=settings.pricing.recalculation_lock_minutes)
        await session.commit()

    mining_client = get_mining_client()
    use_case = RecalculatePricesUseCase(PoolCollectorService(mining_client))
    async with AsyncSessionFactory() as session:
        recalculation = await use_case(session, PriceRecalculationReason.MANUAL if force else PriceRecalculationReason.SCHEDULED)
        state = await session.scalar(
            select(EconomySchedulerState)
            .where(EconomySchedulerState.job_name == PRICE_RECALCULATION_JOB)
            .with_for_update()
        )
        if state is not None:
            state.last_run_at = now
            state.next_run_at = recalculation.next_recalculation_at or now + timedelta(minutes=settings.pricing.recalculation_retry_minutes)
            state.locked_until = None
        await session.commit()

        # Уведомляем ломбард: цены пересчитаны (только при успешном пересчёте)
        if recalculation.status == PriceRecalculationStatus.COMPLETED:
            try:
                economy_events = get_economy_events()
                await economy_events.publish_state_update(
                    event_type="economy_state_updated",
                    payload={
                        "action": "buyout_prices_updated",
                        "location_slug": settings.pawn_shop_location_slug,
                        "initiator_character_id": None,
                    },
                )
            except Exception:
                logger.exception("Failed to publish buyout_prices_updated after recalculation")

        return recalculation
