"""Хаос-сценарий 3: переходы между локациями и вкладками.

B находится в сделке, уходит из локации (CancelDealsForCharacterUseCase),
возвращается, создаёт новую сделку с тем же партнёром, система находит
ту же живую сделку, B добавляет деньги, A и B подтверждают, сделка
завершается — активы переходят корректно.
"""

from datetime import timedelta

import pytest

from mining_app.apps.items.deals.enums import (
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
)
from shared.schemas.deal_events import DealEventType
from tests.chaos._world import (
    ClockPatch,
    add_item,
    create_deal,
    default_world,
    make_user,
    set_ducats,
)

pytestmark = pytest.mark.asyncio


async def test_location_transition_preserves_live_deal():
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    start_a = world.character(A).ducats
    start_b = world.character(B).ducats

    # B кладёт деньги -> предложение B не пустое
    await set_ducats(world, deal.id, B, 1000)
    assert world.offer(deal.id, B).ducats_escrowed == 1000

    # B уходит из локации и оффлайн -> авто-отмена сделок B
    world.move_character(B, "other.place", online=False)
    cancelled = await world.ucs.cancel_for_character(B)
    assert cancelled >= 1
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.ACTIVE  # сделка ЖИВА
    assert deal_entity.cancelled_by_character_id == B

    # B возвращается
    world.move_character(B, "1.13.forge", online=True)

    # A создаёт новую сделку с тем же партнёром
    new_deal = await create_deal(world, A, B)
    assert new_deal.status == DealStatus.DRAFT

    # B ищет ЖИВЫЕ сделки (ACTIVE или DRAFT) — старая сделка найдена
    lst = await world.ucs.list(make_user(B), [DealStatus.ACTIVE, DealStatus.DRAFT], 10, 0)
    found_ids = {d.id for d in lst.objects}
    assert deal.id in found_ids, "Старая сделка должна быть найдена в списке"
    assert new_deal.id in found_ids, "Новая сделка тоже должна быть в списке"

    # B повторно кладёт деньги в СТАРУЮ сделку (cancelled_by_character_id стирается)
    await set_ducats(world, deal.id, B, 500)
    assert world.offer(deal.id, B).ducats_escrowed == 500
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.cancelled_by_character_id is None
    assert deal_entity.cancelled_at is None

    # A кладёт предмет в старую сделку (используем существующий спецификации)
    sword = world.give_item(A, "s1")
    await add_item(world, deal.id, A, sword.id)

    # Оба подтверждают
    await world.ucs.confirm(deal.id, make_user(A))
    await world.ucs.confirm(deal.id, make_user(B))

    assert world.store.deals[deal.id].status == DealStatus.COMPLETED
    # Предмет -> B, деньги -> A минус налог (10%, A - инициатор = продавец предмета)
    assert world.inventory(sword.id).character_id == B
    # A получил 500 - 50 налог = 450
    assert world.character(A).ducats == start_a + 450
    assert world.character(B).ducats == start_b - 500

    # Ledger
    ops = [op for op in world.store.ledger_list if op.deal_id == deal.id]
    tax_ops = [op for op in ops if op.operation_kind == DealLedgerOperationKind.TAX]
    assert len(tax_ops) == 1
    assert tax_ops[0].amount == 50
    for op in ops:
        assert op.status == DealLedgerOperationStatus.APPLIED


async def test_cancel_for_character_does_not_expire_other_deal():
    world, A, B = default_world()
    deal1 = await create_deal(world, A, B)
    await world.ucs.accept(deal1.id, make_user(B))

    # A создаёт вторую сделку с B
    deal2 = await create_deal(world, B, A)  # меняем роли: B инициатор, A партнёр
    await world.ucs.accept(deal2.id, make_user(A))

    # B уходит -> CancelDealsForCharacterUseCase(B) отменяет все сделки B
    world.move_character(B, "other.place", online=False)
    cancelled = await world.ucs.cancel_for_character(B)
    assert cancelled >= 2  # обе сделки содержат B

    # Обе сделки ЖИВЫ
    assert world.store.deals[deal1.id].status == DealStatus.ACTIVE
    assert world.store.deals[deal2.id].status == DealStatus.ACTIVE