"""Хаос-сценарий 7: полная жизнь сделки от создания до завершения.

A создаёт сделку -> B принимает (DRAFT -> ACTIVE) -> A кладёт меч ->
B кладёт 500 дукатов -> A видит налог (10% без лицензии) ->
оба подтверждают -> меч переходит к B, деньги переходят к A минус налог ->
статус COMPLETED, повторный вызов confirm идемпотентен.
"""

from decimal import Decimal

import pytest

from mining_app.apps.items.deals.enums import (
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
)
from shared.schemas.deal_events import DealEventType

from tests.chaos._world import (
    add_item,
    create_deal,
    default_world,
    make_user,
    set_ducats,
)

pytestmark = pytest.mark.asyncio


async def test_full_deal_life_cycle():
    """Полный цикл жизни сделки: создание -> принятие -> предложения -> подтверждение -> завершение."""
    world, A, B = default_world()
    start_a = world.character(A).ducats
    start_b = world.character(B).ducats

    # 1. A создаёт сделку (DRAFT)
    deal = await create_deal(world, A, B)
    assert deal.status == DealStatus.DRAFT
    assert deal.initiator_character_id == A
    assert deal.partner_character_id == B

    # 2. B принимает (DRAFT -> ACTIVE)
    result = await world.ucs.accept(deal.id, make_user(B))
    assert result.status == DealStatus.ACTIVE
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.ACTIVE
    assert deal_entity.expires_at is not None

    # 3. A кладёт меч
    sword = world.give_item(A, "s1")
    await add_item(world, deal.id, A, sword.id)
    assert world.inventory(sword.id).deal_id == deal.id

    # 4. B кладёт 500 дукатов
    await set_ducats(world, deal.id, B, Decimal("500"))
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("500")
    assert world.character(B).ducats == start_b - Decimal("500")

    # 5. Проверяем офферы напрямую (без detail)
    assert world.offer(deal.id, A).ducats_escrowed == Decimal("0")  # A кладет предмет, не деньги
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("500")

    # 6. A подтверждает
    await world.ucs.confirm(deal.id, make_user(A))
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.initiator_confirmed_at is not None
    assert deal_entity.partner_confirmed_at is None  # B ещё не подтвердил

    # 7. B подтвершает -> сделка завершена
    result = await world.ucs.confirm(deal.id, make_user(B))
    assert result.status == DealStatus.COMPLETED

    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.COMPLETED
    assert deal_entity.completed_at is not None
    assert deal_entity.initiator_confirmed_at is not None
    assert deal_entity.partner_confirmed_at is not None

    # 8. Меч перешёл к B, деньги перешли к A минус налог (10% = 50)
    assert world.inventory(sword.id).character_id == B, "Меч должен перейти к B"
    assert world.inventory(sword.id).deal_id is None, "Меч освобождён из сделки"
    assert world.character(A).ducats == start_a + Decimal("450"), \
        f"A должен получить 450 (500 - 50 налог), а получил {world.character(A).ducats - start_a}"
    assert world.character(B).ducats == start_b - Decimal("500"), \
        f"B должен потратить 500, а потратил {start_b - world.character(B).ducats}"

    # 9. Ledger: операции проведены
    ops = [op for op in world.store.ledger_list if op.deal_id == deal.id]
    transfer_ops = [op for op in ops if op.operation_kind == DealLedgerOperationKind.TRANSFER]
    tax_ops = [op for op in ops if op.operation_kind == DealLedgerOperationKind.TAX]
    assert len(transfer_ops) >= 1, "Должна быть хотя бы одна TRANSFER операция"
    assert len(tax_ops) == 1, f"TAX должен быть ровно 1, а не {len(tax_ops)}"
    assert tax_ops[0].amount == Decimal("50"), f"Налог 10% от 500 = 50, а не {tax_ops[0].amount}"
    for op in ops:
        assert op.status == DealLedgerOperationStatus.APPLIED

    # 10. Событие завершения
    completed_events = [e for e in world.store.events if e[0] == DealEventType.COMPLETED]
    assert len(completed_events) == 1, "Событие завершения должно быть ровно одно"

    # 11. Идемпотентность confirm: повторный вызов на COMPLETED не меняет состояние
    try:
        await world.ucs.confirm(deal.id, make_user(B))
    except Exception:
        pass  # сделка уже завершена — состояние ошибки допустимо
    assert world.character(A).ducats == start_a + Decimal("450")
    assert world.character(B).ducats == start_b - Decimal("500")
    assert world.inventory(sword.id).character_id == B