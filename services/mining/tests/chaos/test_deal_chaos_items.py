"""Хаос-сценарий 2: предметы, экипировка, возврат из эскроу, повторное открытие.

Имитирует реального игрока внутри сделки:
  B кладёт 3 предмета -> снимает 1 -> надевает предмет из инвентаря ->
  пытается положить НАДЕТЫЙ предмет (ошибка DealAssetUnavailableError) ->
  снимает -> кладёт снова -> отменяет сделку (возврат ВСЕХ предметов) ->
  надевает один из них -> создает новую сделку с тем же партнером:
  система находит ТУ ЖЕ живую сделку (updated_at desc) -> кладет предмет ->
  оба подтверждают -> завершение и корректный переход активов.
"""

from decimal import Decimal

import pytest

from mining_app.apps.items.deals.enums import (
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
)
from shared.schemas.deal_events import DealEventType
from mining_app.apps.items.deals.exceptions import DealAssetUnavailableError

from tests.chaos._world import (
    add_item,
    create_deal,
    default_world,
    make_user,
    remove_item,
    set_ducats,
)

pytestmark = pytest.mark.asyncio


def _deal_item_for(world, deal_id, inv_id):
    """Найти DealItem по inventory_item_id внутри сделки."""
    for it in world.store.items.values():
        if it.deal_id == deal_id and it.inventory_item_id == inv_id:
            return it
    return None


async def test_item_chaos_equip_unequip_and_reopen_same_live_deal():
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    # ── Инвентарь B: 3 предмета ──
    s1 = world.give_item(B, "s1")
    s2 = world.give_item(B, "s2")
    s3 = world.give_item(B, "s3")

    start_ducats_b = world.character(B).ducats
    start_ducats_a = world.character(A).ducats

    # B кладёт 3 предмета
    await add_item(world, deal.id, B, s1.id)
    await add_item(world, deal.id, B, s2.id)
    await add_item(world, deal.id, B, s3.id)
    assert world.inventory(s1.id).deal_id == deal.id
    assert world.inventory(s2.id).deal_id == deal.id
    assert world.inventory(s3.id).deal_id == deal.id

    # B снимает 1 предмет (s3) — s3 возвращается в инвентарь (deal_id = None)
    await remove_item(world, deal.id, B, _deal_item_for(world, deal.id, s3.id).id)
    assert world.inventory(s3.id).deal_id is None

    # B надевает снятый предмет (s3) — deal_id уже None, поэтому проверка
    # "Предмет надет" срабатывает раньше, чем "уже в сделке"
    world.equip(B, s3.id)
    assert s3.id in world.store.equipped

    # Попытка положить НАДЕТЫЙ предмет -> DealAssetUnavailableError
    with pytest.raises(DealAssetUnavailableError) as exc:
        await add_item(world, deal.id, B, s3.id)
    assert exc.value.error_code == "DEAL_ASSET_UNAVAILABLE"

    # B снимает надетый и кладёт его снова
    world.unequip(B, s3.id)
    await add_item(world, deal.id, B, s3.id)
    assert world.inventory(s3.id).deal_id == deal.id
    deal_item_count = len([it for it in world.store.items.values() if it.deal_id == deal.id])
    assert deal_item_count == 3

    # ── Отмена B: ВСЕ предметы возвращаются в инвентарь B ──
    await world.ucs.cancel(deal.id, B)
    for inv in (s1, s2, s3):
        assert world.inventory(inv.id).deal_id is None, f"item {inv.id} завис в эскроу"
        assert world.inventory(inv.id).character_id == B, f"item {inv.id} переехал не туда"
    assert world.character(B).ducats == start_ducats_b, "Баланс B изменился при отмене"
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.ACTIVE  # сделка ЖИВА
    assert deal_entity.cancelled_by_character_id == B

    # ── B надевает один из вернувшихся предметов (s3) ──
    world.equip(B, s3.id)
    with pytest.raises(DealAssetUnavailableError) as exc2:
        await add_item(world, deal.id, B, s3.id)
    assert exc2.value.error_code == "DEAL_ASSET_UNAVAILABLE"
    world.unequip(B, s3.id)

    # ── B создаёт НОВУЮ сделку с тем же партнёром A ──
    new_deal = await create_deal(world, A, B)
    assert new_deal.status == DealStatus.DRAFT

    # B ищет ЖИВЫЕ сделки (ACTIVE) — старая сделка найдена по updated_at desc
    lst = await world.ucs.list(make_user(B), [DealStatus.ACTIVE], 10, 0)
    active_deals = [d for d in lst.objects]
    assert len(active_deals) == 1, f"Должна быть ровно 1 живая сделка, а не {len(active_deals)}"
    assert active_deals[0].id == deal.id, "Система нашла СТАРУЮ сделку, а не новую"

    # ── B кладёт предмет (s1) и A кладёт деньги в СТАРУЮ сделку ──
    await set_ducats(world, deal.id, A, Decimal("1200"))
    await add_item(world, deal.id, B, s1.id)
    assert world.inventory(s1.id).deal_id == deal.id
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("0")
    assert world.offer(deal.id, A).ducats_escrowed == Decimal("1200")

    # ── Оба подтверждают -> завершение ──
    await world.ucs.confirm(deal.id, make_user(A))
    result = await world.ucs.confirm(deal.id, make_user(B))

    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.COMPLETED
    assert deal_entity.completed_at is not None

    # s1 перешёл к A (покупателю), деньги — к B (продавцу) минус налог
    assert world.inventory(s1.id).character_id == A, "Предмет должен перейти к A"
    assert world.inventory(s1.id).deal_id is None, "Предмет должен быть освобождён из сделки"
    # A потерял 1200 дт (переведено покупателем), B получил 1080 дт (1200 - 120 налог 10%)
    assert world.character(A).ducats == start_ducats_a - Decimal("1200")
    assert world.character(B).ducats == start_ducats_b + Decimal("1080"), \
        f"B должен получить 1080 (1200 - 120 налог), а получил {world.character(B).ducats - start_ducats_b}"

    # Ledger: 1 ESCROW_HOLD (A deposit), 1 TRANSFER (money), 1 TAX (10%)
    deal_ops = [op for op in world.store.ledger_list if op.deal_id == deal.id]
    hold_ops = [op for op in deal_ops if op.operation_kind == DealLedgerOperationKind.ESCROW_HOLD]
    transfer_ops = [op for op in deal_ops if op.operation_kind == DealLedgerOperationKind.TRANSFER]
    tax_ops = [op for op in deal_ops if op.operation_kind == DealLedgerOperationKind.TAX]
    assert len(hold_ops) == 1, f"ESCROW_HOLD должен быть ровно 1, а не {len(hold_ops)}"
    assert len(transfer_ops) == 1, f"TRANSFER должен быть ровно 1, а не {len(transfer_ops)}"
    assert len(tax_ops) == 1, f"TAX должен быть ровно 1, а не {len(tax_ops)}"
    assert tax_ops[0].amount == Decimal("120"), f"Налог 10% от 1200 = 120, а не {tax_ops[0].amount}"
    for op in deal_ops:
        assert op.status == DealLedgerOperationStatus.APPLIED

    # Идемпотентность confirm: повторный вызов не должен дважды переводить активы
    # (сделка уже COMPLETED — повторный confirm B допускает состояние COMPLETED,
    #  но не должен изменить балансы)
    deal_ops_before = len(deal_ops)
    try:
        await world.ucs.confirm(deal.id, make_user(B))
    except Exception:
        pass  # сделка уже завершена — состояние ошибки допустимо идемпотентным образом
    assert world.character(B).ducats == start_ducats_b + Decimal("1080")
    assert world.inventory(s1.id).character_id == A

    # Событие завершения сделки
    completed_events = [e for e in world.store.events if e[0] == DealEventType.COMPLETED]
    assert len(completed_events) == 1, "Событие завершения должно быть ровно одно"