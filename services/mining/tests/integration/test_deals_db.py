"""Интеграционные тесты СДЕЛОК (mining) на реальной тестовой БД echo_test.

Дефекты фиксируются characterization-тестами test_defect_min*_*: они
закрепляют текущее (неверное) поведение как документацию бага.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from mining_app.apps.items.deals.enums import (
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
    ResourceReservationStatus,
)
from mining_app.apps.items.deals.exceptions import (
    DealAssetUnavailableError,
    DealBothSidesMoneyError,
    DealCompletionError,
    DealInsufficientFundsError,
    DealPriceTooLowError,
    DealSelfPartnerError,
)
from mining_app.apps.items.deals.models import (
    Deal,
    DealItem,
    DealOffer,
    DealLedgerOperation,
    DealResourceReservation,
)
from mining_app.apps.items.deals.schemas import (
    DealCreateSchema,
    DealCurrencyOfferUpdateSchema,
    DealResourceOfferUpdateSchema,
)
from mining_app.apps.resources import models as resources_models

from .conftest import (
    make_active_deal_with_offer,
    seed_character_resource,
    seed_resource,
    user,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")

INIT_ID = uuid.uuid4()
PARTNER_ID = uuid.uuid4()


# ==========================================================================
# 1. Создание сделки
# ==========================================================================

async def test_create_deal_persists_draft_with_two_offers(ucs):
    ucs.char_client.online_ids = {INIT_ID, PARTNER_ID}

    deal = await ucs.create_uc(user(INIT_ID), DealCreateSchema(
        partner_character_id=PARTNER_ID, location_slug="1.13.forge"))

    row = await ucs.session.get(Deal, deal.id)
    assert row is not None
    assert row.status == DealStatus.DRAFT
    assert row.initiator_character_id == INIT_ID
    assert row.partner_character_id == PARTNER_ID

    offer_rows = (await ucs.session.execute(
        select(DealOffer).where(DealOffer.deal_id == deal.id))).scalars().all()
    assert {o.character_id for o in offer_rows} == {INIT_ID, PARTNER_ID}
    assert all(o.revision == 0 for o in offer_rows)


async def test_create_deal_self_partner_rejected_no_rows(ucs):
    with pytest.raises(DealSelfPartnerError):
        await ucs.create_uc(user(INIT_ID), DealCreateSchema(
            partner_character_id=INIT_ID, location_slug="1.13.forge"))

    count = await ucs.session.scalar(select(sa.func.count()).select_from(Deal))
    assert count == 0, "Отклонённая сделка не должна оставлять строк в БД"


# ==========================================================================
# 2. Добавление ресурса + резервирование
# ==========================================================================

async def test_add_resource_creates_deal_item_and_active_reservation(ucs):
    ucs.char_client.online_ids = {INIT_ID, PARTNER_ID}
    await seed_resource(ucs.session, slug="iron", price=100, weight=2)
    await seed_character_resource(ucs.session, INIT_ID, "iron", 100)

    deal = await ucs.create_uc(user(INIT_ID), DealCreateSchema(
        partner_character_id=PARTNER_ID, location_slug="1.13.forge"))
    item = await ucs.add_res_uc(deal.id, "iron", user(INIT_ID),
                                DealResourceOfferUpdateSchema(amount=10))

    db_item = await ucs.session.get(DealItem, item.id)
    assert db_item is not None and db_item.amount == 10
    assert db_item.asset_type.value == "RESOURCE"

    reservation = (await ucs.session.execute(
        select(DealResourceReservation).where(
            DealResourceReservation.deal_item_id == item.id))).scalar_one()
    assert reservation.status == ResourceReservationStatus.ACTIVE
    assert reservation.amount == 10


async def test_add_resource_insufficient_balance_rejected_persists_nothing(ucs):
    ucs.char_client.online_ids = {INIT_ID, PARTNER_ID}
    await seed_resource(ucs.session, slug="iron", price=100)
    await seed_character_resource(ucs.session, INIT_ID, "iron", 5)  # мало

    deal = await ucs.create_uc(user(INIT_ID), DealCreateSchema(
        partner_character_id=PARTNER_ID, location_slug="1.13.forge"))
    with pytest.raises(DealAssetUnavailableError):
        await ucs.add_res_uc(deal.id, "iron", user(INIT_ID),
                             DealResourceOfferUpdateSchema(amount=10))

    items_count = await ucs.session.scalar(
        select(sa.func.count()).select_from(DealItem))
    assert items_count == 0


# ==========================================================================
# 3. Эскроу дукатов
# ==========================================================================

async def test_set_ducats_escrow_updates_offer_writes_ledger_and_debits_wallet(ucs):
    ucs.char_client.online_ids = {INIT_ID, PARTNER_ID}
    await seed_resource(ucs.session, slug="iron", price=100)
    await seed_character_resource(ucs.session, PARTNER_ID, "iron", 50)

    deal = await ucs.create_uc(user(PARTNER_ID), DealCreateSchema(
        partner_character_id=INIT_ID, location_slug="1.13.forge"))
    op_id = uuid.uuid4()
    offer = await ucs.set_ducats_uc(deal.id, user(PARTNER_ID),
                                    DealCurrencyOfferUpdateSchema(
                                        amount=Decimal("600"), operation_id=op_id))

    assert offer.ducats_amount == Decimal("600")
    assert offer.ducats_escrowed == Decimal("600")

    ledger = (await ucs.session.execute(select(DealLedgerOperation))).scalars().all()
    holds = [op for op in ledger if op.operation_kind == DealLedgerOperationKind.ESCROW_HOLD]
    assert len(holds) == 1
    assert holds[0].operation_id == op_id
    assert holds[0].amount == Decimal("600")
    assert holds[0].status == DealLedgerOperationStatus.APPLIED

    debits = [c for c in ucs.char_client.calls if c[0] == "debit_ducats"]
    assert len(debits) == 1 and debits[0][2] == 600.0


async def test_set_ducats_insufficient_funds_rejected_and_no_ledger(ucs):
    ucs.char_client.online_ids = {INIT_ID, PARTNER_ID}
    ucs.char_client.ducats_balances[PARTNER_ID] = Decimal("10")
    await seed_resource(ucs.session, slug="iron", price=100)
    await seed_character_resource(ucs.session, PARTNER_ID, "iron", 50)

    deal = await ucs.create_uc(user(PARTNER_ID), DealCreateSchema(
        partner_character_id=INIT_ID, location_slug="1.13.forge"))
    with pytest.raises(DealInsufficientFundsError):
        await ucs.set_ducats_uc(deal.id, user(PARTNER_ID),
                                DealCurrencyOfferUpdateSchema(
                                    amount=Decimal("600"), operation_id=uuid.uuid4()))
    ledger_count = await ucs.session.scalar(
        select(sa.func.count()).select_from(DealLedgerOperation))
    assert ledger_count == 0


async def test_defect_min01_negative_ducats_blocked_only_by_pydantic_schema(ucs):
    """DEFECT MIN-01: защита от отрицательной суммы для DUCATS живёт ТОЛЬКО в
    Pydantic-схеме (Field ge=0); в use-case проверка есть лишь в ветке GOLD,
    а на уровне БД CHECK отсутствует (см. MIN-02)."""
    from pydantic import ValidationError

    ucs.char_client.online_ids = {INIT_ID, PARTNER_ID}
    await seed_resource(ucs.session, slug="iron", price=100)

    deal = await ucs.create_uc(user(INIT_ID), DealCreateSchema(
        partner_character_id=PARTNER_ID, location_slug="1.13.forge"))
    with pytest.raises(ValidationError):
        await ucs.set_ducats_uc(deal.id, user(INIT_ID),
                                DealCurrencyOfferUpdateSchema(
                                    amount=Decimal("-50"), operation_id=uuid.uuid4()))



# ==========================================================================
# 4. Сквозной жизненный цикл: confirm → confirm → complete
# ==========================================================================

async def _confirmed_active_deal(ucs, init_id=INIT_ID, partner_id=PARTNER_ID,
                                 iron_amount=10, iron_price=100, ducats=600):
    deal = await make_active_deal_with_offer(
        ucs, init_id, partner_id,
        iron_amount=iron_amount, iron_price=iron_price, ducats=ducats)
    # Переводим сделку в ACTIVE (как делает AcceptDealUseCase)
    await ucs.session.execute(sa.update(Deal).where(Deal.id == deal.id)
                              .values(status=DealStatus.ACTIVE))
    await ucs.session.commit()
    return deal


async def test_full_lifecycle_confirm_confirm_completes_and_transfers(ucs):
    deal = await _confirmed_active_deal(ucs)

    res1 = await ucs.confirm_uc(deal.id, user(INIT_ID))
    assert res1.status == DealStatus.ACTIVE  # подтверждён только инициатор
    row = await ucs.session.get(Deal, deal.id)
    assert row.initiator_confirmed_at is not None
    assert row.partner_confirmed_at is None
    # чтение выше открыло неявную транзакцию — закрываем (в проде сессия
    # на каждый запрос новая; здесь эмулируем это откатом)
    await ucs.session.rollback()

    res2 = await ucs.confirm_uc(deal.id, user(PARTNER_ID))
    assert res2.status == DealStatus.COMPLETED
    await ucs.session.rollback()

    row = await ucs.session.get(Deal, deal.id)
    assert row.completed_at is not None

    init_res = await ucs.session.scalar(select(resources_models.CharacterResource)
                                        .where(resources_models.CharacterResource.character_id == INIT_ID))
    part_res = await ucs.session.scalar(select(resources_models.CharacterResource)
                                        .where(resources_models.CharacterResource.character_id == PARTNER_ID))
    assert init_res.amount == 90   # 100 - 10
    assert part_res.amount == 10   # получил ресурсы

    reservation = (await ucs.session.execute(select(DealResourceReservation))).scalar_one()
    assert reservation.status == ResourceReservationStatus.TRANSFERRED

    ledger = (await ucs.session.execute(select(DealLedgerOperation))).scalars().all()
    transfers = [op for op in ledger if op.operation_kind == DealLedgerOperationKind.TRANSFER]
    taxes = [op for op in ledger if op.operation_kind == DealLedgerOperationKind.TAX]
    assert len(transfers) == 1 and transfers[0].amount == Decimal("600")
    assert len(taxes) == 1 and taxes[0].amount == Decimal("60.00")  # 10% без лицензии


async def test_confirm_rejects_too_cheap_offer(ucs):
    # товар стоит 10 * 100 = 1000 дт; минимум 50% => 500; предлагаем 100
    deal = await _confirmed_active_deal(ucs, ducats=100)
    with pytest.raises(DealPriceTooLowError):
        await ucs.confirm_uc(deal.id, user(PARTNER_ID))


async def test_set_ducats_on_both_sides_rejected_in_db_flow(ucs):
    # чисто денежный сценарий: партнёр внёс эскроу, инициатор тоже пытается
    ucs.char_client.online_ids = {INIT_ID, PARTNER_ID}
    await seed_resource(ucs.session, slug="iron", price=100)

    deal = await ucs.create_uc(user(INIT_ID), DealCreateSchema(
        partner_character_id=PARTNER_ID, location_slug="1.13.forge"))
    await ucs.set_ducats_uc(deal.id, user(PARTNER_ID),
                            DealCurrencyOfferUpdateSchema(
                                amount=Decimal("600"), operation_id=uuid.uuid4()))
    with pytest.raises(DealBothSidesMoneyError):
        await ucs.set_ducats_uc(deal.id, user(INIT_ID),
                                DealCurrencyOfferUpdateSchema(
                                    amount=Decimal("300"), operation_id=uuid.uuid4()))


# ==========================================================================
# 5. Отмена стороны и истечение сделки
# ==========================================================================

async def test_cancel_side_refunds_escrow_and_keeps_deal_alive(ucs):
    deal = await make_active_deal_with_offer(ucs, INIT_ID, PARTNER_ID)  # DRAFT: эскроу 600 у партнёра

    result = await ucs.cancel_uc(deal.id, PARTNER_ID)
    assert result.cancelled_by_character_id == PARTNER_ID

    row = await ucs.session.get(Deal, deal.id)
    assert row.status == DealStatus.DRAFT  # сделка остаётся живой (by design)

    offer = (await ucs.session.execute(
        select(DealOffer).where(DealOffer.character_id == PARTNER_ID))).scalar_one()
    assert offer.ducats_amount == Decimal("0")
    assert offer.ducats_escrowed == Decimal("0")

    ledger = (await ucs.session.execute(select(DealLedgerOperation))).scalars().all()
    refunds = [op for op in ledger
               if op.operation_kind == DealLedgerOperationKind.ESCROW_RELEASE]
    assert len(refunds) == 1 and refunds[0].amount == Decimal("600")

    credits = [c for c in ucs.char_client.calls if c[0] == "credit_ducats"]
    assert credits and credits[0][2] == 600.0


async def test_expire_refunds_escrow_and_marks_expired(ucs):
    deal = await make_active_deal_with_offer(ucs, INIT_ID, PARTNER_ID)  # эскроу 600 у партнёра
    await ucs.session.execute(sa.update(Deal).where(Deal.id == deal.id)
                              .values(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
    await ucs.session.commit()

    expired_count = await ucs.expire_uc()
    assert expired_count == 1

    row = await ucs.session.get(Deal, deal.id)
    assert row.status == DealStatus.EXPIRED

    reservation = (await ucs.session.execute(select(DealResourceReservation))).scalar_one()
    assert reservation.status == ResourceReservationStatus.RELEASED

    ledger = (await ucs.session.execute(select(DealLedgerOperation))).scalars().all()
    assert any(op.operation_kind == DealLedgerOperationKind.ESCROW_RELEASE
               and op.amount == Decimal("600") for op in ledger)



# ==========================================================================
# 6. Лимит веса при завершении
# ==========================================================================

async def test_complete_blocked_when_recipient_overweight_no_asset_moves(ucs):
    deal = await _confirmed_active_deal(ucs)
    # подтверждаем оба оффера — сделка готова к завершению
    await ucs.session.execute(sa.update(DealOffer)
                              .where(DealOffer.deal_id == deal.id)
                              .values(confirmed_revision=DealOffer.revision))
    await ucs.session.commit()
    # Партнёр почти при лимите: входящие 10 железа * вес 2 = 20 не влезают
    ucs.char_client.weight_balances[PARTNER_ID] = type(
        "B", (), {"weight": 9990, "max_weight": 10000})()

    with pytest.raises(DealCompletionError):
        await ucs.complete_uc(deal.id)

    row = await ucs.session.get(Deal, deal.id)
    assert row.status == DealStatus.ACTIVE  # транзакция откатилась
    init_res = await ucs.session.scalar(select(resources_models.CharacterResource)
                                        .where(resources_models.CharacterResource.character_id == INIT_ID))
    assert init_res.amount == 100  # ресурсы не тронуты
    payouts = [c for c in ucs.char_client.calls if c[0] == "credit_ducats"]
    assert payouts == []  # деньги не выплачены


# ==========================================================================
# 7. Контракты БД (CHECK-ограничения) и дефекты схемы
# ==========================================================================

async def test_db_constraint_positive_amount_on_deal_items(ucs, db_session):
    ucs.char_client.online_ids = {INIT_ID, PARTNER_ID}
    await seed_resource(db_session, slug="iron", price=100)
    deal = await ucs.create_uc(user(INIT_ID), DealCreateSchema(
        partner_character_id=PARTNER_ID, location_slug="1.13.forge"))
    offer = (await db_session.execute(select(DealOffer).where(
        DealOffer.deal_id == deal.id, DealOffer.character_id == INIT_ID))).scalar_one()

    bad_item = DealItem(deal_id=deal.id, offer_id=offer.id,
                        owner_character_id=INIT_ID, asset_type="RESOURCE",
                        resource_slug="iron", amount=-5)
    db_session.add(bad_item)
    with pytest.raises(sa.exc.IntegrityError):
        await db_session.commit()


async def test_db_constraint_same_initiator_and_partner_rejected(db_session):
    bad_deal = Deal(initiator_character_id=INIT_ID, partner_character_id=INIT_ID,
                    location_slug="1.13.forge", status=DealStatus.DRAFT,
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=30))
    db_session.add(bad_deal)
    with pytest.raises(sa.exc.IntegrityError):
        await db_session.commit()


async def test_db_constraint_positive_amount_on_deal_offers(ucs, db_session):
    """CHECK-констрейнты на ducats_*/gold_* колонках deal_offers
    отклоняют отрицательный эскроу (MIN-02 починен)."""
    ucs.char_client.online_ids = {INIT_ID, PARTNER_ID}
    deal = await ucs.create_uc(user(INIT_ID), DealCreateSchema(
        partner_character_id=PARTNER_ID, location_slug="1.13.forge"))
    offer = (await db_session.execute(select(DealOffer).where(
        DealOffer.deal_id == deal.id, DealOffer.character_id == INIT_ID))).scalar_one()
    offer.ducats_amount = Decimal("-123.45")
    offer.ducats_escrowed = Decimal("-123.45")
    
    with pytest.raises(IntegrityError):
        await db_session.commit()
    
    await db_session.rollback()


# MIN-03 (RecoverCompletingDealsUseCase падал InvalidRequestError из-за
# общей сессии) ПОЧИНЕН разработчиками: items/depends.py теперь создаёт
# раздельные recover_session / complete_session. Регрессионный тест
# перенесён в test_complete_deal_db.py::
#   test_recovery_completes_stuck_completing_deal_across_sessions

