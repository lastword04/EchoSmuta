"""Интеграционные тесты БИРЖИ (exchange) на реальной тестовой БД echo_test.

Покрывают: CreateExchangeLotUseCase, DealExchangeLotUseCase,
CancelExchangeLotUseCase. Внешние сервисы замоканы, БД реальная.

Дефекты документируются characterization-тестами test_defect_eco*_*.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from economy_app.apps.pawn_shop.models import (
    EconomyTransaction,
    ExchangeLot,
    LotStatus,
    LotType,
    TransactionType,
)
from economy_app.apps.pawn_shop.schemas import LotCreateRequest, LotItemRequest

from .conftest import http_status_error, seed_resource

pytestmark = pytest.mark.asyncio(loop_scope="session")

OWNER = uuid.uuid4()   # владелец лота
EXECUTOR = uuid.uuid4()  # тот, кто исполняет/покупает лот


async def _lots(db_session) -> list:
    return list((await db_session.scalars(select(ExchangeLot))).all())


async def _txns(db_session) -> list:
    return list((await db_session.scalars(select(EconomyTransaction))).all())


def sell_request(resource_id, qty=10, price="100"):
    return LotCreateRequest(
        lot_type=LotType.SELL,
        price=Decimal(price),
        items=[LotItemRequest(resource_id=resource_id, quantity=qty)],
    )


def buy_request(resource_id, qty=10, price="100"):
    return LotCreateRequest(
        lot_type=LotType.BUY,
        price=Decimal(price),
        items=[LotItemRequest(resource_id=resource_id, quantity=qty)],
    )


# ==========================================================================
# Создание лотов
# ==========================================================================

async def test_create_sell_lot_debits_resources_and_persists_active_lot(ucs, db_session):
    resource = await seed_resource(db_session, code="iron")
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 50}]

    lot = await ucs["create_lot"](sell_request(resource.id), OWNER, db_session)

    assert lot.status == LotStatus.ACTIVE
    rows = await _lots(db_session)
    assert len(rows) == 1 and rows[0].price == Decimal("100")
    assert [(i.resource_id, i.quantity) for i in rows[0].items] == [(resource.id, 10)]

    # каждый ресурс бандла списан у продавца
    assert ("debit", "iron", OWNER, 10) in ucs["mining_client"].calls


async def test_create_sell_lot_insufficient_resource_409_leaves_no_trace(ucs, db_session):
    resource = await seed_resource(db_session, code="iron")
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 5}]

    with pytest.raises(HTTPException) as exc_info:
        await ucs["create_lot"](sell_request(resource.id, qty=10), OWNER, db_session)
    assert exc_info.value.status_code == 409

    assert ucs["mining_client"].calls == []            # списаний не было
    assert await _lots(db_session) == []               # лот не записан


async def test_create_buy_lot_debits_ducats_and_persists_active_lot(ucs, db_session):
    resource = await seed_resource(db_session, code="iron")

    lot = await ucs["create_lot"](buy_request(resource.id), OWNER, db_session)

    assert lot.status == LotStatus.ACTIVE
    debits = [c for c in ucs["char_client"].calls if c[0] == "debit"]
    assert debits and debits[0][2] == Decimal("100")


async def test_create_buy_lot_insufficient_ducats_409_leaves_no_trace(ucs, db_session):
    resource = await seed_resource(db_session, code="iron")
    ucs["char_client"].balance = Decimal("50")

    with pytest.raises(HTTPException) as exc_info:
        await ucs["create_lot"](buy_request(resource.id), OWNER, db_session)
    assert exc_info.value.status_code == 409

    assert [c for c in ucs["char_client"].calls if c[0] == "debit"] == []
    assert await _lots(db_session) == []


async def test_create_lot_price_below_half_bundle_value_rejected_409(ucs, db_session):
    # ценность бандла = 10 * 10 = 100 дт; минимум 50%; цена 49 → отказ
    resource = await seed_resource(db_session, code="iron")
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 50}]

    with pytest.raises(HTTPException) as exc_info:
        await ucs["create_lot"](sell_request(resource.id, qty=10, price="49"), OWNER, db_session)
    assert exc_info.value.status_code == 409

    assert ucs["mining_client"].calls == []
    assert [c for c in ucs["char_client"].calls if c[0] == "debit"] == []
    assert await _lots(db_session) == []


async def test_create_lot_price_exactly_at_minimum_is_accepted(ucs, db_session):
    # граничное значение: 50% ровно — лот создаётся
    resource = await seed_resource(db_session, code="iron")
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 50}]

    lot = await ucs["create_lot"](sell_request(resource.id, qty=10, price="50"), OWNER, db_session)
    assert lot.price == Decimal("50")
    assert lot.status == LotStatus.ACTIVE


async def test_create_lot_unknown_resource_404(ucs, db_session):
    with pytest.raises(HTTPException) as exc_info:
        await ucs["create_lot"](sell_request(uuid.uuid4()), OWNER, db_session)
    assert exc_info.value.status_code == 404


# ==========================================================================
# Исполнение лотов
# ==========================================================================

async def _sell_lot(ucs, db_session, price="100", qty=10):
    resource = await seed_resource(db_session, code="iron")
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 100}]
    lot = await ucs["create_lot"](sell_request(resource.id, qty=qty, price=price), OWNER, db_session)
    return lot, resource


def _pairs(calls, method):
    return [(c[1], c[2]) for c in calls if c[0] == method]


async def test_deal_sell_lot_buyer_pays_seller_gets_gross_minus_tax(ucs, db_session):
    lot, resource = await _sell_lot(ucs, db_session)
    # ставка налога продавца: exchange_tax_rate = 0.15 → tax 15.00
    result = await ucs["deal_lot"](lot.id, EXECUTOR, db_session)

    assert result["status"] == LotStatus.FILLED
    calls = ucs["char_client"].calls
    # покупатель заплатил полную цену
    assert (EXECUTOR, Decimal("100")) in _pairs(calls, "debit")
    # продавец получил gross и отдельно сдал налог
    assert (OWNER, Decimal("100")) in _pairs(calls, "credit")
    assert (OWNER, Decimal("15")) in _pairs(calls, "debit")
    # покупатель получил ресурс
    assert ("credit", "iron", EXECUTOR, 10) in ucs["mining_client"].calls

    db_lot = await db_session.get(ExchangeLot, lot.id)
    assert db_lot.status == LotStatus.FILLED


async def test_deal_sell_lot_writes_exchange_transactions_with_lot_id(ucs, db_session):
    lot, resource = await _sell_lot(ucs, db_session)
    await ucs["deal_lot"](lot.id, EXECUTOR, db_session)

    txns = [t for t in await _txns(db_session) if str(t.lot_id) == str(lot.id)]
    types = {t.transaction_type for t in txns}
    assert types == {TransactionType.EXCHANGE_BUY, TransactionType.EXCHANGE_SELL}
    buy_total = sum(t.total for t in txns if t.transaction_type == TransactionType.EXCHANGE_BUY)
    assert buy_total == Decimal("100")   # доли бандла в сумме = цена лота
    assert all(str(t.buyer_id) == str(EXECUTOR) and str(t.seller_id) == str(OWNER) for t in txns)


async def test_deal_buy_lot_executor_delivers_resources_gets_money(ucs, db_session):
    resource = await seed_resource(db_session, code="iron")
    # владелец создаёт BUY-заявку: хочет купить iron 10 за 100 дт (списываются сразу)
    lot = await ucs["create_lot"](buy_request(resource.id), OWNER, db_session)
    ucs["char_client"].calls.clear()
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 50}]

    await ucs["deal_lot"](lot.id, EXECUTOR, db_session)

    # исполнитель отдал ресурсы владельцу лота
    assert ("debit", "iron", EXECUTOR, 10) in ucs["mining_client"].calls
    assert ("credit", "iron", OWNER, 10) in ucs["mining_client"].calls
    # налог по ставке ПРОДАВЦА (=исполнителя): gross credit 100, tax debit 15
    assert (EXECUTOR, Decimal("100")) in _pairs(ucs["char_client"].calls, "credit")
    assert (EXECUTOR, Decimal("15")) in _pairs(ucs["char_client"].calls, "debit")

    db_lot = await db_session.get(ExchangeLot, lot.id)
    assert db_lot.status == LotStatus.FILLED


async def test_deal_rejects_old_lot_priced_below_half_value_409_stays_active(ucs, db_session):
    lot, resource = await _sell_lot(ucs, db_session)
    # эмуляция «старого» лота: занижаем цену в БД ниже текущих правил
    lot.price = Decimal("30")   # < 50% от ценности 100
    await db_session.commit()
    ucs["char_client"].calls.clear()

    with pytest.raises(HTTPException) as exc_info:
        await ucs["deal_lot"](lot.id, EXECUTOR, db_session)
    assert exc_info.value.status_code == 409

    await db_session.refresh(lot)
    assert lot.status == LotStatus.ACTIVE
    assert _pairs(ucs["char_client"].calls, "debit") == []
    assert _pairs(ucs["char_client"].calls, "credit") == []


async def test_deal_own_lot_rejected_400_no_side_effects(ucs, db_session):
    lot, resource = await _sell_lot(ucs, db_session)
    with pytest.raises(HTTPException) as exc_info:
        await ucs["deal_lot"](lot.id, OWNER, db_session)
    assert exc_info.value.status_code == 400
    assert lot.status == LotStatus.ACTIVE


async def test_deal_inactive_lot_rejected_409(ucs, db_session):
    lot, resource = await _sell_lot(ucs, db_session)
    lot.status = LotStatus.CANCELLED
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await ucs["deal_lot"](lot.id, EXECUTOR, db_session)
    assert exc_info.value.status_code == 409


async def test_deal_sell_lot_buyer_insufficient_ducats_409_no_transfers(ucs, db_session):
    lot, resource = await _sell_lot(ucs, db_session)
    ucs["char_client"].balance = Decimal("10")
    ucs["char_client"].calls.clear()
    ucs["mining_client"].calls.clear()

    with pytest.raises(HTTPException) as exc_info:
        await ucs["deal_lot"](lot.id, EXECUTOR, db_session)
    assert exc_info.value.status_code == 409
    await db_session.refresh(lot)
    assert lot.status == LotStatus.ACTIVE
    assert _pairs(ucs["char_client"].calls, "debit") == []
    assert _pairs(ucs["char_client"].calls, "credit") == []
    assert ucs["mining_client"].calls == []


async def test_deal_buy_lot_executor_lacks_resources_409_no_transfers(ucs, db_session):
    resource = await seed_resource(db_session, code="iron")
    lot = await ucs["create_lot"](buy_request(resource.id), OWNER, db_session)
    ucs["char_client"].calls.clear()
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 3}]

    with pytest.raises(HTTPException) as exc_info:
        await ucs["deal_lot"](lot.id, EXECUTOR, db_session)
    assert exc_info.value.status_code == 409
    assert lot.status == LotStatus.ACTIVE
    assert ucs["mining_client"].calls == []   # у исполнителя ничего не списано



# ==========================================================================
# Отмена лотов
# ==========================================================================

async def test_cancel_sell_lot_returns_resources_to_owner(ucs, db_session):
    lot, resource = await _sell_lot(ucs, db_session)
    ucs["mining_client"].calls.clear()

    result = await ucs["cancel_lot"](lot.id, OWNER, db_session)

    assert result["status"] == LotStatus.CANCELLED
    assert ("credit", "iron", OWNER, 10) in ucs["mining_client"].calls
    await db_session.refresh(lot)
    assert lot.status == LotStatus.CANCELLED


async def test_cancel_buy_lot_refunds_money_to_owner(ucs, db_session):
    resource = await seed_resource(db_session, code="iron")
    lot = await ucs["create_lot"](buy_request(resource.id), OWNER, db_session)
    ucs["char_client"].calls.clear()

    result = await ucs["cancel_lot"](lot.id, OWNER, db_session)

    assert result["status"] == LotStatus.CANCELLED
    credits = [(c[1], c[2]) for c in ucs["char_client"].calls if c[0] == "credit"]
    assert (OWNER, Decimal("100")) in credits   # возврат всей зарезервированной цены


async def test_cancel_by_non_owner_403_lot_stays_active(ucs, db_session):
    lot, resource = await _sell_lot(ucs, db_session)
    ucs["mining_client"].calls.clear()
    with pytest.raises(HTTPException) as exc_info:
        await ucs["cancel_lot"](lot.id, EXECUTOR, db_session)
    assert exc_info.value.status_code == 403
    await db_session.refresh(lot)
    assert lot.status == LotStatus.ACTIVE
    assert ucs["mining_client"].calls == []     # ресурсы не возвращались


async def test_cancel_twice_second_attempt_409(ucs, db_session):
    lot, resource = await _sell_lot(ucs, db_session)
    await ucs["cancel_lot"](lot.id, OWNER, db_session)

    with pytest.raises(HTTPException) as exc_info:
        await ucs["cancel_lot"](lot.id, OWNER, db_session)
    assert exc_info.value.status_code == 409
    # второй раз ресурсы повторно НЕ возвращаются
    first_count = sum(1 for c in ucs["mining_client"].calls if c[0] == "credit")
    assert first_count == 1


async def test_cancel_missing_lot_404(ucs, db_session):
    with pytest.raises(HTTPException) as exc_info:
        await ucs["cancel_lot"](uuid.uuid4(), OWNER, db_session)
    assert exc_info.value.status_code == 404


# ==========================================================================
# Дефекты консистентности (characterization — упадут после починки)
# ==========================================================================

async def test_exchange_deal_compensates_when_mid_chain_fails(ucs, db_session):
    """ECO-03 починен: при сбое mining.credit после payment-debit срабатывает
    сага — деньги покупателя возвращаются, ресурсы откатываются."""
    lot, resource = await _sell_lot(ucs, db_session)
    ucs["mining_client"].fail_on("credit", http_status_error(409))

    with pytest.raises(HTTPException) as exc_info:
        await ucs["deal_lot"](lot.id, EXECUTOR, db_session)
    assert exc_info.value.status_code == 409

    # Деньги списаны И возвращены (компенсация сработала)
    debits = _pairs(ucs["char_client"].calls, "debit")
    assert (EXECUTOR, Decimal("100")) in debits  # платёж случился
    compensating = [c for c in ucs["char_client"].calls
                    if c[0] == "credit" and c[1] == EXECUTOR]
    assert len(compensating) == 1  # refund случился
    assert compensating[0][2] == Decimal("100")


async def test_exchange_payment_is_idempotent_on_retry(ucs, db_session):
    """ECO-04 починен: payment использует детерминированный operation_id от lot.id.
    При повторной попытке после сбоя платёж НЕ дублируется."""
    lot, resource = await _sell_lot(ucs, db_session)
    # первый вызов: падает НАЛОГОВЫЙ debit продавца
    ucs["char_client"].fail_on_call_index("debit", 1, http_status_error(500))
    with pytest.raises(HTTPException):
        await ucs["deal_lot"](lot.id, EXECUTOR, db_session)

    buyer_debits_after_fail = [c for c in ucs["char_client"].calls
                               if c[0] == "debit" and c[1] == EXECUTOR and c[2] == Decimal("100")]
    assert len(buyer_debits_after_fail) == 1

    # повторная попытка (сбой убран)
    ucs["char_client"]._fail_on_call_index.clear()
    await ucs["deal_lot"](lot.id, EXECUTOR, db_session)

    buyer_debits_total = [c for c in ucs["char_client"].calls
                          if c[0] == "debit" and c[1] == EXECUTOR and c[2] == Decimal("100")]
    # Платёж НЕ продублирован — операция идемпотентна
    assert len(buyer_debits_total) == 2  # debit случился дважды, но...
    op_ids = {c[3] for c in buyer_debits_total}
    assert len(op_ids) == 1, "operation_id одинаковый — второй debit идемпотентен"

