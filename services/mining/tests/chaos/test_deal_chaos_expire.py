"""Хаос-сценарий 5: экспирация сделок.

Имитирует истечение срока жизни сделки:
  B кладёт деньги -> время сдвигается вперёд до истечения expires_at ->
  ExpireDealUseCase срабатывает -> деньги возвращаются -> статус EXPIRED.
"""

from datetime import timedelta
from decimal import Decimal

import pytest

from mining_app.apps.items.deals.enums import (
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
)

from tests.chaos._world import (
    ClockPatch,
    create_deal,
    default_world,
    make_user,
    set_ducats,
)

pytestmark = pytest.mark.asyncio


async def test_expire_returns_escrow_and_marks_expired():
    """B кладёт деньги, время истекает -> деньги возвращаются, статус EXPIRED."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    start_b = world.character(B).ducats

    # B кладёт 500 дукатов
    await set_ducats(world, deal.id, B, Decimal("500"))
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("500")
    assert world.character(B).ducats == start_b - Decimal("500")

    # Время сдвигается вперёд на 31 минуту (expires_at ~ 30 минут)
    with ClockPatch(world, advance=timedelta(minutes=31)):
        expired_count = await world.ucs.expire()
        assert expired_count >= 1

    # Статус сделки — EXPIRED
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.EXPIRED

    # Деньги вернулись к B
    assert world.character(B).ducats == start_b, \
        f"B должен получить свой эскроу обратно: {world.character(B).ducats} != {start_b}"


async def test_expire_is_idempotent():
    """Повторный вызов expire на EXPIRED сделке не должен вызывать ошибок."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    start_b = world.character(B).ducats

    # B кладёт деньги
    await set_ducats(world, deal.id, B, Decimal("300"))

    # Первая экспирация
    with ClockPatch(world, advance=timedelta(minutes=31)):
        await world.ucs.expire()
    assert world.store.deals[deal.id].status == DealStatus.EXPIRED
    assert world.character(B).ducats == start_b

    # Повторная экспирация — идемпотентна
    with ClockPatch(world, advance=timedelta(minutes=60)):
        await world.ucs.expire()
    assert world.store.deals[deal.id].status == DealStatus.EXPIRED
    assert world.character(B).ducats == start_b  # Баланс не изменился повторно


async def test_expire_does_not_affect_active_deals():
    """Expire не трогает сделки, которые ещё не истекли."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    start_b = world.character(B).ducats
    await set_ducats(world, deal.id, B, Decimal("200"))

    # Время сдвигается только на 15 минут (меньше 30-минутного лимита)
    with ClockPatch(world, advance=timedelta(minutes=15)):
        expired_count = await world.ucs.expire()
        assert expired_count == 0

    # Сделка остаётся ACTIVE
    assert world.store.deals[deal.id].status == DealStatus.ACTIVE
    # Деньги НЕ вернулись
    assert world.character(B).ducats == start_b - Decimal("200")
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("200")