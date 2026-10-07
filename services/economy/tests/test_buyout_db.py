"""Интеграционные тесты скупки (buyout) на реальной БД echo_test.

Дефекты документируются characterization-тестами test_defect_eco*_*.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from economy_app.apps.pawn_shop.models import (
    BuyoutStock,
    EconomyTransaction,
    TransactionType,
)
from economy_app.apps.pawn_shop.schemas import TradeRequest

from .conftest import http_status_error, seed_resource

pytestmark = pytest.mark.asyncio(loop_scope="session")

CHAR_ID = uuid.uuid4()


async def _stock(db_session, resource_id) -> int:
    row = await db_session.scalar(
        select(BuyoutStock).where(BuyoutStock.resource_id == resource_id))
    return row.quantity if row else 0


async def _txns(db_session) -> list:
    return list((await db_session.scalars(select(EconomyTransaction))).all())


# ==========================================================================
# Продажа ресурсов скупке
# ==========================================================================

async def test_sell_to_buyout_happy_path(ucs, db_session):
    resource = await seed_resource(db_session, stock=100)
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 50}]

    result = await ucs["sell"](TradeRequest(resource_id=resource.id, quantity=10),
                               CHAR_ID, db_session)

    assert result["total_price"] == Decimal("80.00")   # 10 * 8.00
    assert await _stock(db_session, resource.id) == 110

    txns = await _txns(db_session)
    assert len(txns) == 1
    assert txns[0].transaction_type == TransactionType.BUYOUT_SELL
    assert txns[0].quantity == 10
    assert txns[0].price_per_unit == Decimal("8.00")
    assert str(txns[0].seller_id) == str(CHAR_ID)

    assert ("debit", "iron", CHAR_ID, 10) in ucs["mining_client"].calls
    credits = [c for c in ucs["char_client"].calls if c[0] == "credit"]
    assert credits and credits[0][2] == Decimal("80.00")


async def test_sell_without_enough_resource_rejected_409_no_side_effects(ucs, db_session):
    resource = await seed_resource(db_session, stock=100)
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 5}]

    with pytest.raises(HTTPException) as exc_info:
        await ucs["sell"](TradeRequest(resource_id=resource.id, quantity=10),
                          CHAR_ID, db_session)
    assert exc_info.value.status_code == 409

    assert await _stock(db_session, resource.id) == 100      # не изменился
    assert ucs["mining_client"].calls == []                   # debit не вызывался
    assert await _txns(db_session) == []                      # транзакций нет


async def test_sell_refunds_resources_when_credit_fails(ucs, db_session):
    """ECO-02 починен: если characters.credit падает, use-case возвращает
    уже списанный ресурс. Игрок не теряет ресурсы."""
    resource = await seed_resource(db_session, stock=100)
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 50}]
    ucs["char_client"].fail_on("credit", http_status_error(409))

    with pytest.raises(HTTPException) as exc_info:
        await ucs["sell"](TradeRequest(resource_id=resource.id, quantity=10),
                          CHAR_ID, db_session)
    assert exc_info.value.status_code == 409

    # Ресурс списан И возвращён (компенсация сработала)
    debits = [c for c in ucs["mining_client"].calls if c[0] == "debit"]
    credits = [c for c in ucs["mining_client"].calls if c[0] == "credit"]
    assert debits and debits[0][1] == "iron" and debits[0][3] == 10  # debit случился
    assert credits and credits[0][1] == "iron" and credits[0][3] == 10  # refund случился


# ==========================================================================
# Покупка ресурсов со скупки
# ==========================================================================

async def test_buy_from_buyout_happy_path(ucs, db_session):
    resource = await seed_resource(db_session, stock=100)

    result = await ucs["buy"](TradeRequest(resource_id=resource.id, quantity=10),
                              CHAR_ID, db_session)

    assert result["total_price"] == Decimal("120.00")  # 10 * 12.00
    assert await _stock(db_session, resource.id) == 90

    txns = await _txns(db_session)
    assert len(txns) == 1
    assert txns[0].transaction_type == TransactionType.BUYOUT_BUY
    assert str(txns[0].buyer_id) == str(CHAR_ID)

    debits = [c for c in ucs["char_client"].calls if c[0] == "debit"]
    assert debits and debits[0][2] == Decimal("120.00")
    assert ("credit", "iron", CHAR_ID, 10) in ucs["mining_client"].calls


async def test_buy_insufficient_stock_rejected_409(ucs, db_session):
    resource = await seed_resource(db_session, stock=5)

    with pytest.raises(HTTPException) as exc_info:
        await ucs["buy"](TradeRequest(resource_id=resource.id, quantity=10),
                         CHAR_ID, db_session)
    assert exc_info.value.status_code == 409

    assert await _stock(db_session, resource.id) == 5
    assert [c for c in ucs["char_client"].calls if c[0] == "debit"] == []
    assert await _txns(db_session) == []


async def test_buy_insufficient_balance_rejected_409(ucs, db_session):
    resource = await seed_resource(db_session, stock=100)
    ucs["char_client"].balance = Decimal("1")

    with pytest.raises(HTTPException) as exc_info:
        await ucs["buy"](TradeRequest(resource_id=resource.id, quantity=10),
                         CHAR_ID, db_session)
    assert exc_info.value.status_code == 409

    assert [c for c in ucs["char_client"].calls if c[0] == "debit"] == []
    assert await _txns(db_session) == []


async def test_buy_refunds_when_delivery_fails(ucs, db_session):
    """ECO-01 починен: если mining.credit падает, use-case делает refund
    уже списанных дукатов. Игрок не теряет деньги."""
    resource = await seed_resource(db_session, stock=100)
    ucs["mining_client"].fail_on("credit", http_status_error(409))

    with pytest.raises(HTTPException) as exc_info:
        await ucs["buy"](TradeRequest(resource_id=resource.id, quantity=10),
                         CHAR_ID, db_session)
    assert exc_info.value.status_code == 409

    # Деньги списаны И возвращены (компенсация сработала)
    debits = [c for c in ucs["char_client"].calls if c[0] == "debit"]
    credits = [c for c in ucs["char_client"].calls if c[0] == "credit"]
    assert debits and debits[0][2] == Decimal("120.00")  # debit случился
    assert credits and credits[0][2] == Decimal("120.00")  # refund случился

# ==========================================================================
# Валидация справочников и точность сумм
# ==========================================================================

async def test_sell_when_price_not_initialized_rejected_409(ucs, db_session):
    resource = await seed_resource(db_session, sell_price=None, buy_price=None, stock=None)

    with pytest.raises(HTTPException) as exc_info:
        await ucs["sell"](TradeRequest(resource_id=resource.id, quantity=1),
                          CHAR_ID, db_session)
    assert exc_info.value.status_code == 409


async def test_unknown_resource_rejected_404(ucs, db_session):
    with pytest.raises(HTTPException) as exc_info:
        await ucs["buy"](TradeRequest(resource_id=uuid.uuid4(), quantity=1),
                         CHAR_ID, db_session)
    assert exc_info.value.status_code == 404


async def test_non_tradeable_city_resource_rejected_400(ucs, db_session):
    resource = await seed_resource(db_session, code="bread", tradeable=False)

    with pytest.raises(HTTPException) as exc_info:
        await ucs["sell"](TradeRequest(resource_id=resource.id, quantity=1),
                          CHAR_ID, db_session)
    assert exc_info.value.status_code == 400


async def test_total_price_decimal_quantization_in_db(ucs, db_session):
    # 3 * 8.33 = 24.99 — округление при записи в Numeric(18,2)
    resource = await seed_resource(db_session, buy_price="8.33", stock=50)
    ucs["mining_client"].player_resources = [{"resource_slug": "iron", "amount": 10}]

    result = await ucs["sell"](TradeRequest(resource_id=resource.id, quantity=3),
                               CHAR_ID, db_session)
    assert result["total_price"] == Decimal("24.99")

