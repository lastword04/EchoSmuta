"""Хаос-сценарий 1: многократный цикл эскроу — главный регресс.

Персонаж B кладёт 100 дт → отменяет → кладёт 200 дт → отменяет →
кладёт 50 дт (A в это время кладёт предмет) → отменяет.

Проверяем на КАЖДОМ шаге:
  * деньги и предметы вернулись владельцам (никаких зависаний в эскроу);
  * сделка остаётся ЖИВОЙ (статус не меняется, expires_at продлевается);
  * каждый новый цикл эскроу создаёт НОВЫЙ operation_id cancel-refund
    (ключ включает ревизию оффера);
  * ledger: PENDING → APPLIED, без «потерянных» строк.
"""

import asyncio
from decimal import Decimal
from types import SimpleNamespace

import pytest

from mining_app.apps.items.deals.enums import (
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
)
from mining_app.apps.items.deals.use_cases import _operation_id

from tests.chaos._world import (
    add_item,
    create_deal,
    default_world,
    make_user,
    set_ducats,
)

pytestmark = pytest.mark.asyncio


def _offer_ops(world, deal_id, cid):
    return [op for op in world.store.ledger_list if op.deal_id == deal_id
            and op.character_id == cid]


async def test_escrow_cycles_refund_every_time_with_new_operation_id():
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    start_ducats = world.character(B).ducats  # 30000
    refund_ids = []

    def assert_balance_restored():
        assert world.character(B).ducats == start_ducats, "деньги не вернулись на баланс B"

    # ── Цикл 1: B кладёт 100 дт и отменяет ──
    await set_ducats(world, deal.id, B, 100)
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("100")
    assert world.character(B).ducats == start_ducats - 100
    rev1 = world.offer(deal.id, B).revision

    await world.ucs.cancel(deal.id, B)
    assert_balance_restored()
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("0")
    refund_ids.append(_operation_id(deal.id, f"{B}:DUCATS:cancel-refund:{rev1}"))

    # Сделка жива: статус не меняется, expires_at продлевается
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.ACTIVE
    assert deal_entity.cancelled_by_character_id == B

    # ── Цикл 2: B кладёт 200 дт и отменяет ──
    await set_ducats(world, deal.id, B, 200)
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("200")
    rev2 = world.offer(deal.id, B).revision
    assert rev2 > rev1, "новый эскроу обязан поднять ревизию оффера"

    await world.ucs.cancel(deal.id, B)
    assert_balance_restored()
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("0")
    refund_ids.append(_operation_id(deal.id, f"{B}:DUCATS:cancel-refund:{rev2}"))

    # ── Цикл 3: B кладёт 50 дт, A кладёт предмет, B отменяет ──
    sword = world.give_item(A, "s1")
    await add_item(world, deal.id, A, sword.id)
    assert world.inventory(sword.id).deal_id == deal.id, "предмет A должен быть в эскроу"

    await set_ducats(world, deal.id, B, 50)
    rev3 = world.offer(deal.id, B).revision
    await world.ucs.cancel(deal.id, B)
    assert_balance_restored()
    assert world.offer(deal.id, B).ducats_escrowed == Decimal("0")
    refund_ids.append(_operation_id(deal.id, f"{B}:DUCATS:cancel-refund:{rev3}"))

    # Деньги B вернулись; предмет A остался в эскроу (не «раскручен» чужим cancel)
    assert world.inventory(sword.id).deal_id == deal.id

    # A снимает свою сторону — предмет возвращается
    await world.ucs.cancel(deal.id, A)
    assert world.inventory(sword.id).deal_id is None
    assert world.inventory(sword.id).character_id == A, "предмет должен вернуться в инвентарь A"
    assert world.offer(deal.id, A).revision > 0

    # ДЕЛО ИДЁТ К ЖИЗНИ ВЕСЬ ПУТЬ: ни один статус не стал финальным
    deal_entity = world.store.deals[deal.id]
    assert deal_entity.status == DealStatus.ACTIVE
    assert deal_entity.cancelled_by_character_id == A  # последний «отменивший»

    # ── Каждый цикл эскроу породил СВОЙ operation_id (уникален) ──
    assert len(set(refund_ids)) == 3, f"operation_id повторился: {refund_ids}"
    assert len(set(map(str, refund_ids))) == 3

    # ── Ledger: PENDING -> APPLIED, никаких зависших PENDING-строк ──
    b_ops = _offer_ops(world, deal.id, B)
    holds = [op for op in b_ops if op.operation_kind == DealLedgerOperationKind.ESCROW_HOLD]
    releases = [op for op in b_ops if op.operation_kind == DealLedgerOperationKind.ESCROW_RELEASE]
    assert len(holds) == 3, "должно быть ровно 3 эскроу-холда (100/200/50)"
    assert len(releases) == 3, "должно быть ровно 3 отмены-возврата"
    for op in holds + releases:
        assert op.status == DealLedgerOperationStatus.APPLIED, \
            f"ledger-операция зависла в статусе {op.status}"

    # Суммы на возврат совпадают с суммами эскроу
    assert {op.amount for op in holds} == {Decimal("100"), Decimal("200"), Decimal("50")}
    assert {op.amount for op in releases} == {Decimal("100"), Decimal("200"), Decimal("50")}


async def test_repeat_cancel_is_idempotent_and_does_not_double_refund():
    """Повторная отмена с той же (неувеличенной) ревизией — без двойного возврата."""
    world, A, B = default_world()
    deal = await create_deal(world, A, B)
    await world.ucs.accept(deal.id, make_user(B))

    await set_ducats(world, deal.id, B, 150)
    await world.ucs.cancel(deal.id, B)
    balance_after = world.character(B).ducats

    # Второй вызов cancel (та же ревизия): refund уже APPLIED -> return ранний
    await world.ucs.cancel(deal.id, B)
    assert world.character(B).ducats == balance_after, "двойной возврат денег!"

    # В store должен быть РОВНО один cancel-refund op на эту ревизию
    releases = [op for op in _offer_ops(world, deal.id, B)
                if op.operation_kind == DealLedgerOperationKind.ESCROW_RELEASE]
    assert len(releases) == 1
    assert releases[0].status == DealLedgerOperationStatus.APPLIED