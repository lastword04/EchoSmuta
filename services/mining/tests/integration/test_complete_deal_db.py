"""Интеграционные тесты CompleteDealUseCase (mining) на реальной БД echo_test.

Покрывают: налоги (обычный/скидочный), payouts и ledger, идемпотентность,
компенсацию при сбое второй транзакции, escrow mismatch, золотые привилегии
и восстановление зависших COMPLETING-сделок (фикс MIN-03: разные сессии).
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from mining_app.apps.items.deals.enums import (
    DealLedgerOperationKind,
    DealStatus,
    ResourceReservationStatus,
)
from mining_app.apps.items.deals.exceptions import (
    DealCompletionError,
    DealGoldTradeDisabledError,
)
from mining_app.apps.items.deals.models import (
    Deal,
    DealItem,
    DealOffer,
    DealLedgerOperation,
    TradeLicense,
)
from mining_app.apps.items.deals.repositories import (
    DealItemRepository,
    DealLedgerOperationRepository,
    DealOfferRepository,
    DealRepository,
    DealResourceReservationRepository,
    TradeLicenseRepository,
)
from mining_app.apps.items.deals.use_cases import CompleteDealUseCase
from mining_app.apps.resources import models as resources_models

from .conftest import make_active_deal_with_offer, seed_resource, user

pytestmark = pytest.mark.asyncio(loop_scope="session")

INIT_ID = uuid.uuid4()
PARTNER_ID = uuid.uuid4()


async def _ledger(ucs):
    rows = (await ucs.session.execute(
        sa.select(DealLedgerOperation))).scalars().all()
    return list(rows)


async def _ready_to_complete(ucs, init_id=INIT_ID, partner_id=PARTNER_ID,
                             iron_amount=10, iron_price=100, ducats=600):
    """Сделка с подтверждёнными офферами, готовая к завершению."""
    deal = await make_active_deal_with_offer(
        ucs, init_id, partner_id,
        iron_amount=iron_amount, iron_price=iron_price, ducats=ducats)
    await ucs.session.execute(sa.update(DealOffer)
                              .where(DealOffer.deal_id == deal.id)
                              .values(confirmed_revision=DealOffer.revision))
    await ucs.session.execute(sa.update(Deal).where(Deal.id == deal.id)
                              .values(status=DealStatus.ACTIVE))
    await ucs.session.commit()
    return deal


# ==========================================================================
# Налоги: обычный и скидочный
# ==========================================================================

async def test_complete_regular_tax_10_percent_without_license(ucs):
    deal = await _ready_to_complete(ucs)

    result = await ucs.complete_uc(deal.id)
    await ucs.session.rollback()

    assert result.status == DealStatus.COMPLETED

    ledger = await _ledger(ucs)
    taxes = [op for op in ledger if op.operation_kind == DealLedgerOperationKind.TAX]
    assert len(taxes) == 1 and taxes[0].amount == Decimal("60.00")   # 10%

    # payout = эскроу минус налог, ушёл получателю денег (партнёру)
    payouts = [c for c in ucs.char_client.calls if c[0] == "credit_ducats"]
    assert payouts and payouts[0][2] == 540.0


async def test_complete_discounted_tax_3_percent_with_active_license(ucs):
    deal = await _ready_to_complete(ucs)
    # получатель денег здесь — ИНИЦИАТОР (плательщик — партнёр);
    # активная лицензия получателя даёт ему скидку налога 3%
    ucs.session.add(TradeLicense(
        character_id=INIT_ID,
        end_date=datetime.now(timezone.utc) + timedelta(days=14)))
    await ucs.session.commit()
    await ucs.session.rollback()

    await ucs.complete_uc(deal.id)
    await ucs.session.rollback()

    ledger = await _ledger(ucs)
    taxes = [op for op in ledger if op.operation_kind == DealLedgerOperationKind.TAX]
    assert len(taxes) == 1 and taxes[0].amount == Decimal("18.00")   # 600 * 3%
    payouts = [c for c in ucs.char_client.calls if c[0] == "credit_ducats"]
    assert payouts and payouts[0][2] == 582.0                        # 600 - 18


# ==========================================================================
# Идемпотентность
# ==========================================================================

async def test_complete_is_idempotent_on_completed_deal(ucs):
    deal = await _ready_to_complete(ucs)
    await ucs.complete_uc(deal.id)
    await ucs.session.rollback()

    # снимок состояния после первого завершения
    calls_snapshot = list(ucs.char_client.calls)
    ledger_count = len((await _ledger(ucs)))
    init_res = await ucs.session.scalar(select(resources_models.CharacterResource)
                                        .where(resources_models.CharacterResource.character_id == INIT_ID))
    await ucs.session.rollback()   # закрываем autobegin от снимка

    result = await ucs.complete_uc(deal.id)   # повторный вызов
    await ucs.session.rollback()

    assert result.status == DealStatus.COMPLETED
    assert ucs.char_client.calls == calls_snapshot, "повторный вызов не должен платить повторно"
    assert len((await _ledger(ucs))) == ledger_count
    await ucs.session.refresh(init_res)
    assert init_res.amount == 90              # ресурсы не списаны второй раз



# ==========================================================================
# Компенсация: сбой второй транзакции после payouts
# ==========================================================================

async def test_compensation_reverses_payouts_when_asset_transfer_fails(ucs):
    """Сбой во ВТОРОЙ транзакции (после выплат): payouts компенсируются
    встречными debit-операциями, активы не переносятся, ledger не пишется."""
    deal = await _ready_to_complete(ucs)
    # ломаем источник ресурсов ПОД подтверждениями: transfer_assets упадёт,
    # т.к. source.amount (5) < item.amount (10). Первая фаза наличие ресурса
    # не проверяет, поэтому payouts успеют пройти.
    await ucs.session.execute(sa.update(resources_models.CharacterResource)
                              .where(resources_models.CharacterResource.character_id == INIT_ID)
                              .values(amount=5))
    await ucs.session.commit()
    ucs.char_client.calls.clear()   # отсекаем вызовы подготовки (эскроу-debit 600)
    await ucs.session.rollback()

    with pytest.raises(ValueError, match="Reserved resource"):
        await ucs.complete_uc(deal.id)

    # 1) выплата прошла и была скомпенсирована встречным списанием
    credits = [c for c in ucs.char_client.calls if c[0] == "credit_ducats"]
    debits = [c for c in ucs.char_client.calls if c[0] == "debit_ducats"]
    assert credits and credits[0][2] == 540.0
    assert len(debits) == 1 and debits[0][2] == 540.0   # compensation

    # 2) активы НЕ перенесены
    init_res = await ucs.session.scalar(select(resources_models.CharacterResource)
                                        .where(resources_models.CharacterResource.character_id == INIT_ID))
    part_res = await ucs.session.scalar(select(resources_models.CharacterResource)
                                        .where(resources_models.CharacterResource.character_id == PARTNER_ID))
    assert init_res.amount == 5
    assert part_res is None

    # 3) ledger второй транзакции откатился (нет TRANSFER/TAX)
    ledger = await _ledger(ucs)
    assert [op for op in ledger
            if op.operation_kind in (DealLedgerOperationKind.TRANSFER,
                                     DealLedgerOperationKind.TAX)] == []

    # 4) сделка осталась в COMPLETING — её подхватит recovery
    row = await ucs.session.get(Deal, deal.id)
    assert row.status == DealStatus.COMPLETING


# ==========================================================================
# Предусловия завершения
# ==========================================================================

async def test_escrow_mismatch_blocks_completion_and_rolls_back(ucs):
    deal = await _ready_to_complete(ucs)
    # расхождение amount/escrowed появляется после подтверждений
    await ucs.session.execute(sa.update(DealOffer)
                              .where(DealOffer.deal_id == deal.id,
                                     DealOffer.character_id == PARTNER_ID)
                              .values(ducats_escrowed=Decimal("500")))
    await ucs.session.commit()
    await ucs.session.rollback()

    with pytest.raises(DealCompletionError, match="Escrow does not match"):
        await ucs.complete_uc(deal.id)

    row = await ucs.session.get(Deal, deal.id)
    assert row.status == DealStatus.ACTIVE          # первая фаза откатилась
    assert [c for c in ucs.char_client.calls if c[0] == "credit_ducats"] == []


async def test_gold_without_trade_privilege_blocks_completion(ucs):
    # эскроу в золоте выставляется при включённой привилегии...
    deal = await make_active_deal_with_offer(ucs, INIT_ID, PARTNER_ID, ducats=None)
    from mining_app.apps.items.deals.schemas import DealCurrencyOfferUpdateSchema
    ucs.char_client.gold_balances[PARTNER_ID] = Decimal("1000")   # золото на кошельке
    await ucs.set_gold_uc(deal.id, user(PARTNER_ID), DealCurrencyOfferUpdateSchema(
        amount=Decimal("10"), operation_id=uuid.uuid4()))     # 10 злт = 700 дт ценности
    await ucs.session.execute(sa.update(Deal).where(Deal.id == deal.id)
                              .values(status=DealStatus.ACTIVE))
    await ucs.session.execute(sa.update(DealOffer)
                              .where(DealOffer.deal_id == deal.id)
                              .values(confirmed_revision=DealOffer.revision))
    await ucs.session.commit()
    # ...а к моменту завершения привилегию отключили
    ucs.char_client.gold_trade_enabled = False
    ucs.char_client.calls.clear()
    with pytest.raises(DealGoldTradeDisabledError):
        await ucs.complete_uc(deal.id)

    row = await ucs.session.get(Deal, deal.id)
    assert row.status == DealStatus.ACTIVE


# ==========================================================================
# Recovery зависших COMPLETING-сделок (регрессия фикса MIN-03)
# ==========================================================================

def _build_complete_stack(session, char_client, events):
    return CompleteDealUseCase(
        DealRepository(session), DealOfferRepository(session),
        DealItemRepository(session), DealResourceReservationRepository(session),
        DealLedgerOperationRepository(session), TradeLicenseRepository(session),
        char_client, deal_tax=0.10, discounted_tax=0.03, deal_events=events,
    )


async def test_recovery_completes_stuck_completing_deal_across_sessions(ucs, engine):
    """Фикс MIN-03: recover и complete работают на РАЗНЫХ сессиях
    (items/depends.py: recover_session / complete_session), поэтому открытая
    autobegin-транзакция списка больше не роняет завершение.
    Воспроизводим продовую топологию и проверяем результат."""
    from mining_app.apps.items.deals.use_cases import RecoverCompletingDealsUseCase

    # 1) зависшая COMPLETING-сделка с валидными данными
    deal = await make_active_deal_with_offer(ucs, INIT_ID, PARTNER_ID)
    await ucs.session.execute(sa.update(DealOffer)
                              .where(DealOffer.deal_id == deal.id)
                              .values(confirmed_revision=DealOffer.revision))
    await ucs.session.execute(sa.update(Deal).where(Deal.id == deal.id)
                              .values(status=DealStatus.COMPLETING))
    await ucs.session.commit()

    # 2) продовая топология: список на одной сессии, complete на другой
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as complete_session:
        complete2 = _build_complete_stack(complete_session, ucs.char_client, ucs.events)
        recover = RecoverCompletingDealsUseCase(DealRepository(ucs.session), complete2)

        # спровоцируем autobegin в сессии списка (условие старого краша MIN-03)
        _ = await ucs.session.scalar(select(sa.func.count()).select_from(Deal))

        recovered = await recover()   # раньше здесь был InvalidRequestError

    assert recovered == 1

    # 3) сделка реально завершена в отдельной сессии, ресурсы переведены
    fresh = factory()
    try:
        row = await fresh.get(Deal, deal.id)
        assert row.status == DealStatus.COMPLETED
        part_res = await fresh.scalar(select(resources_models.CharacterResource)
                                      .where(resources_models.CharacterResource.character_id == PARTNER_ID))
        assert part_res.amount == 10
    finally:
        await fresh.close()

