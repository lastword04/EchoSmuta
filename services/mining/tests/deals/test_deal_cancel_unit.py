"""Юнит-тесты CancelDealUseCase: отмена стороны, возврат эскроу, освобождение активов.

Контракт CancelDealUseCase (см. deals.py: «СДЕЛКА ВСЕГДА ОСТАЁТСЯ ЖИВОЙ»):
- возврат денег ТОЛЬКО отменяющему (PENDING -> HTTP -> APPLIED, идемпотентно по operation_id);
- освобождение ТОЛЬКО его предметов/резерваций;
- обнуление его оффера, сброс подтверждений у обеих сторон;
- статус сделки НЕ меняется.
"""
import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest

from shared.schemas.deal_events import DealEventType

from mining_app.apps.items.deals.enums import (
    DealAssetType,
    DealLedgerOperationKind,
    DealLedgerOperationStatus,
    DealStatus,
    ResourceReservationStatus,
)
from mining_app.apps.items.deals.exceptions import DealAccessDeniedError, DealStateError
from mining_app.apps.items.deals.use_cases import CancelDealUseCase, _operation_id

from tests.deals._fakes import (
    INIT_ID,
    PARTNER_ID,
    FakeCharacterClient,
    FakeEvents,
    FakeLedgerRepo,
    FakeReservationRepo,
    FakeSession,
    make_deal,
    make_deal_item,
    make_offer,
    make_user,
)


def _build(deal, canceller_offer, other_offer, *, deal_items=None,
           inventory_items=None, ledger_by_op=None, reservation=None):
    canceller_offer.deal_id = deal.id
    other_offer.deal_id = deal.id

    async def get_for_update(deal_id):
        return deal

    async def get_for_character(deal_id, character_id, for_update=None):
        return canceller_offer if character_id == canceller_offer.character_id else None

    async def get_by_deal(deal_id, for_update=None):
        return [canceller_offer, other_offer]

    async def items_by_deal(deal_id, for_update=None):
        return deal_items or []

    repository = SimpleNamespace(session=FakeSession(gets=inventory_items or {}), get_for_update=get_for_update)
    offer_repo = SimpleNamespace(get_for_character=get_for_character, get_by_deal=get_by_deal)
    item_repo = SimpleNamespace(get_by_deal=items_by_deal)
    ledger = FakeLedgerRepo(by_operation_id=ledger_by_op)
    client = FakeCharacterClient([INIT_ID, PARTNER_ID])
    events = FakeEvents()
    use_case = CancelDealUseCase(repository, offer_repo, item_repo, FakeReservationRepo(active=reservation), ledger, events, client)
    return use_case, client, ledger, events, repository


@pytest.mark.asyncio
async def test_cancel_by_initiator_refunds_escrow_and_releases_item():
    """Отмена инициатором: возврат его дукатов, освобождение предмета, сброс подтверждений, сделка жива."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID, ducats=500)
    partner_offer = make_offer(PARTNER_ID, confirmed=1)
    inv = SimpleNamespace(id=uuid.uuid4(), deal_id=deal.id)
    deal_item = make_deal_item(INIT_ID, my_offer.id, inventory_item_id=inv.id)
    use_case, client, ledger, events, repository = _build(
        deal, my_offer, partner_offer, deal_items=[deal_item], inventory_items={inv.id: inv},
    )

    rev_before = my_offer.revision
    result = await use_case(deal.id, INIT_ID)

    op_id = _operation_id(deal.id, f"{INIT_ID}:DUCATS:cancel-refund:{rev_before}")
    assert client.credits == [(INIT_ID, Decimal("500"), op_id)]
    assert len(ledger.created) == 1
    assert ledger.created[0].operation_kind == DealLedgerOperationKind.ESCROW_RELEASE
    assert ledger.created[0].status == DealLedgerOperationStatus.PENDING
    assert inv.deal_id is None
    assert deal_item in repository.session.deleted
    assert my_offer.ducats_escrowed == Decimal("0")
    assert my_offer.ducats_amount == Decimal("0")
    assert my_offer.revision == 2
    assert my_offer.confirmed_revision is None
    assert partner_offer.confirmed_revision is None
    assert deal.status == DealStatus.ACTIVE
    assert deal.cancelled_by_character_id == INIT_ID
    assert deal.initiator_confirmed_at is None
    assert result.status == DealStatus.ACTIVE
    assert events.published[-1].event_type == DealEventType.UPDATED


@pytest.mark.asyncio
async def test_cancel_by_partner_refunds_partner_only():
    """Отмена партнёром: возврат ТОЛЬКО ему, оффер инициатора не тронут."""
    deal = make_deal()
    partner_offer = make_offer(PARTNER_ID, ducats=300)
    init_offer = make_offer(INIT_ID, ducats=700)
    use_case, client, *_ = _build(deal, partner_offer, init_offer)

    rev_before = partner_offer.revision
    await use_case(deal.id, PARTNER_ID)

    op_id = _operation_id(deal.id, f"{PARTNER_ID}:DUCATS:cancel-refund:{rev_before}")
    assert client.credits == [(PARTNER_ID, Decimal("300"), op_id)]
    assert init_offer.ducats_escrowed == Decimal("700")
    assert init_offer.revision == 1
    assert deal.cancelled_by_character_id == PARTNER_ID
    assert deal.partner_confirmed_at is None


@pytest.mark.asyncio
async def test_cancel_releases_resource_reservation():
    """Отмена освобождает резервацию ресурса (статус RELEASED)."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID)
    partner_offer = make_offer(PARTNER_ID, ducats=600)
    deal_item = make_deal_item(INIT_ID, my_offer.id, asset_type=DealAssetType.RESOURCE, resource_slug="iron", amount=10)
    reservation = SimpleNamespace(status=ResourceReservationStatus.ACTIVE)
    use_case, *_ = _build(deal, my_offer, partner_offer, deal_items=[deal_item], reservation=reservation)

    await use_case(deal.id, INIT_ID)

    assert reservation.status == ResourceReservationStatus.RELEASED


@pytest.mark.asyncio
async def test_cancel_refund_skipped_when_already_applied():
    """Повторная отмена после проведённого возврата: без HTTP и без новых PENDING-строк."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID, ducats=500)
    partner_offer = make_offer(PARTNER_ID)
    op_id = _operation_id(deal.id, f"{INIT_ID}:DUCATS:cancel-refund:{my_offer.revision}")
    use_case, client, ledger, *_ = _build(
        deal, my_offer, partner_offer,
        ledger_by_op={op_id: SimpleNamespace(status=DealLedgerOperationStatus.APPLIED, amount=Decimal("500"))},
    )

    await use_case(deal.id, INIT_ID)

    assert client.credits == []
    assert ledger.created == []
    assert my_offer.ducats_escrowed == Decimal("0")


@pytest.mark.asyncio
async def test_cancel_completed_deal_raises():
    """Завершённую сделку отменить нельзя."""
    deal = make_deal(status=DealStatus.COMPLETED)
    use_case, client, *_ = _build(deal, make_offer(INIT_ID, ducats=500), make_offer(PARTNER_ID))

    with pytest.raises(DealStateError):
        await use_case(deal.id, INIT_ID)

    assert client.credits == []


@pytest.mark.asyncio
async def test_cancel_by_outsider_raises():
    """Не-участник сделки не может её отменить."""
    deal = make_deal()
    use_case, *_ = _build(deal, make_offer(INIT_ID), make_offer(PARTNER_ID))

    with pytest.raises(DealAccessDeniedError):
        await use_case(deal.id, uuid.uuid4())

@pytest.mark.asyncio
async def test_cancel_refund_repeats_on_new_escrow_cycle():
    """cancel → re-escrow → cancel: вторая отмена возвращает деньги (ключ уникален на цикл эскроу)."""
    deal = make_deal()
    my_offer = make_offer(INIT_ID, ducats=500)
    partner_offer = make_offer(PARTNER_ID)

    # Цикл 1 уже проведён: возврат с ключом ревизии 1 имеет статус APPLIED
    op_id_cycle1 = _operation_id(deal.id, f"{INIT_ID}:DUCATS:cancel-refund:1")
    use_case, client, ledger, *_ = _build(
        deal, my_offer, partner_offer,
        ledger_by_op={op_id_cycle1: SimpleNamespace(status=DealLedgerOperationStatus.APPLIED, amount=Decimal("500"))},
    )

    # Симулируем состояние после первой отмены и повторного эскроу:
    # отмена подняла revision до 2, затем игрок снова положил дукаты
    my_offer.revision = 2
    my_offer.ducats_escrowed = Decimal("500")
    my_offer.ducats_amount = Decimal("500")

    await use_case(deal.id, INIT_ID)

    # Вторая отмена ОБЯЗАНА вернуть деньги: ключ с ревизией 2, а не 1
    op_id_cycle2 = _operation_id(deal.id, f"{INIT_ID}:DUCATS:cancel-refund:2")
    assert client.credits == [(INIT_ID, Decimal("500"), op_id_cycle2)]
    assert len(ledger.created) == 1
    assert ledger.created[0].status == DealLedgerOperationStatus.PENDING
    assert my_offer.ducats_escrowed == Decimal("0")
    assert my_offer.revision == 3
