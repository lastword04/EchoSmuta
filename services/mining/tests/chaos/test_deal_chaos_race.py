"""Хаос-сценарий 4: одновременные действия (race conditions).

Имитирует конфликтующие действия двух участников:
  - A и B одновременно подтверждают -> сделка завершается ровно один раз.
  - A подтвержает, B в этот момент отменяет -> B получает эскроу обратно.
"""

import asyncio
from decimal import Decimal

import pytest

from mining_app.apps.items.deals.enums import (
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
)
from mining_app.apps.items.deals.exceptions import (
    DealEmptyOfferError,
    DealNotReadyError,
)

from tests.chaos._world import (
    create_deal,
    default_world,
    make_user,
    set_ducats,
)

pytestmark = pytest.mark.asyncio


async def test_both_confirm_completes_deal_exactly_once():
    """A и B одновременно подтверждают — сделка завершается ровно один раз."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    start_a = world.character(A).ducats
    start_b = world.character(B).ducats

    # A кладёт предмет, B кладёт деньги
    sword = world.give_item(A, "s1")
    from tests.chaos._world import add_item
    await add_item(world, deal.id, A, sword.id)
    await set_ducats(world, deal.id, B, Decimal("1000"))

    # Оба подтверждают "одновременно" (последовательно, но без промежуточных проверок)
    await world.ucs.confirm(deal.id, make_user(A))
    await world.ucs.confirm(deal.id, make_user(B))

    # Сделка завершена
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.COMPLETED
    assert deal_entity.completed_at is not None

    # Предмет -> B, деньги -> A минус налог (10% = 100)
    assert world.inventory(sword.id).character_id == B
    assert world.character(B).ducats == start_b - Decimal("1000")
    assert world.character(A).ducats == start_a + Decimal("900")

    # Ledger: ровно 1 TRANSFER и 1 TAX
    ops = [op for op in world.store.ledger_list if op.deal_id == deal.id]
    transfer_ops = [op for op in ops if op.operation_kind == DealLedgerOperationKind.TRANSFER]
    tax_ops = [op for op in ops if op.operation_kind == DealLedgerOperationKind.TAX]
    assert len(transfer_ops) == 1, f"TRANSFER должен быть ровно 1, а не {len(transfer_ops)}"
    assert len(tax_ops) == 1, f"TAX должен быть ровно 1, а не {len(tax_ops)}"
    assert tax_ops[0].amount == Decimal("100")
    for op in ops:
        assert op.status == DealLedgerOperationStatus.APPLIED


async def test_confirm_and_cancel_conflict():
    """A подтверждает, B в этот момент отменяет — B получает эскроу обратно."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    start_a = world.character(A).ducats
    start_b = world.character(B).ducats

    # A кладёт предмет, B кладёт деньги
    sword = world.give_item(A, "s1")
    from tests.chaos._world import add_item
    await add_item(world, deal.id, A, sword.id)
    await set_ducats(world, deal.id, B, Decimal("800"))

    # A подтвержает
    await world.ucs.confirm(deal.id, make_user(A))

    # B отменяет — получает свой эскроу (800 дукатов) обратно
    await world.ucs.cancel(deal.id, B)

    # Баланс B вернулся к исходному (деньги вернулись)
    assert world.character(B).ducats == start_b, \
        f"B должен получить свой эскроу обратно: {world.character(B).ducats} != {start_b}"
    # Предмет остаётся у A (не перешёл к B)
    assert world.inventory(sword.id).character_id == A

    # Сделка жива, но предложение B снято
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.ACTIVE
    assert deal_entity.cancelled_by_character_id == B

    # A снимает подтверждение, но НЕ может поменять предмет на деньги
    # (DealMixedOfferError: нельзя мешать предметы и деньги в одном оффере)
    from mining_app.apps.items.deals.exceptions import DealMixedOfferError
    with pytest.raises(DealMixedOfferError):
        await set_ducats(world, deal.id, A, Decimal("500"))

    # Состояние сделки не изменилось после ошибки
    assert world.character(B).ducats == start_b
    assert world.inventory(sword.id).character_id == A
    assert world.offer(deal.id, A).ducats_escrowed == Decimal("0")