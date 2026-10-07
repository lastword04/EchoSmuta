"""Параллельные действия сторон (asyncio.gather) на фейках — смоук конкурентного вызова.

Реальные гонки блокируются FOR UPDATE-локами БД (проверяется интеграционными
тестами); здесь проверяем, что юз-кейсы не падают и сохраняют инварианты,
обе стороны вызываются одновременно в одном цикле событий.
"""
import asyncio
import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest

from mining_app.apps.items.deals.enums import DealStatus
from mining_app.apps.items.deals.use_cases import CancelDealUseCase, ConfirmDealUseCase

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


def _build_confirm(deal, init_offer, partner_offer, items):
    init_offer.deal_id = deal.id
    partner_offer.deal_id = deal.id

    async def get_for_participant(deal_id, cid, for_update=None):
        return deal

    async def get_by_deal(deal_id, for_update=None):
        return [init_offer, partner_offer]

    async def items_by_deal(deal_id, for_update=None):
        return items

    async def incoming_weight(deal_id, cid):
        return 0

    repository = SimpleNamespace(session=FakeSession(rows=[("sword", Decimal("1000"))]), get_for_participant=get_for_participant)
    offer_repo = SimpleNamespace(get_by_deal=get_by_deal)
    item_repo = SimpleNamespace(get_by_deal=items_by_deal, incoming_weight=incoming_weight)
    events = FakeEvents()
    completed = []

    async def complete(deal_id):
        completed.append(deal_id)
        return None

    use_case = ConfirmDealUseCase(repository, offer_repo, item_repo, complete, FakeCharacterClient([INIT_ID, PARTNER_ID]), events)
    return use_case, completed


@pytest.mark.asyncio
async def test_gather_both_confirms_completes_deal():
    """Обе стороны подтверждают «одновременно»: оба подтверждения зафиксированы, завершение вызвано."""
    deal = make_deal()
    init_offer = make_offer(INIT_ID)
    partner_offer = make_offer(PARTNER_ID, ducats=600)
    items = [make_deal_item(INIT_ID, init_offer.id, snapshot={"item_slug": "sword"})]
    use_case, completed = _build_confirm(deal, init_offer, partner_offer, items)

    await asyncio.gather(
        use_case(deal.id, make_user(INIT_ID)),
        use_case(deal.id, make_user(PARTNER_ID)),
    )

    assert init_offer.confirmed_revision == init_offer.revision
    assert partner_offer.confirmed_revision == partner_offer.revision
    assert len(completed) >= 1
    assert deal.initiator_confirmed_at is not None
    assert deal.partner_confirmed_at is not None


def _build_cancel(deal, offers_by_cid):
    for offer in offers_by_cid.values():
        offer.deal_id = deal.id

    async def get_for_update(deal_id):
        return deal

    async def get_for_character(deal_id, character_id, for_update=None):
        return offers_by_cid.get(character_id)

    async def get_by_deal(deal_id, for_update=None):
        return list(offers_by_cid.values())

    async def items_by_deal(deal_id, for_update=None):
        return []

    repository = SimpleNamespace(session=FakeSession(), get_for_update=get_for_update)
    offer_repo = SimpleNamespace(get_for_character=get_for_character, get_by_deal=get_by_deal)
    item_repo = SimpleNamespace(get_by_deal=items_by_deal)
    ledger = FakeLedgerRepo()
    client = FakeCharacterClient([INIT_ID, PARTNER_ID])
    events = FakeEvents()
    use_case = CancelDealUseCase(repository, offer_repo, item_repo, FakeReservationRepo(), ledger, events, client)
    return use_case, client


@pytest.mark.asyncio
async def test_gather_both_cancels_refunds_both_sides():
    """Обе стороны отменяют «одновременно»: каждый получает свой возврат, сделка жива, подтверждений нет."""
    deal = make_deal()
    init_offer = make_offer(INIT_ID, ducats=400)
    partner_offer = make_offer(PARTNER_ID, ducats=400)
    use_case, client = _build_cancel(deal, {INIT_ID: init_offer, PARTNER_ID: partner_offer})

    await asyncio.gather(
        use_case(deal.id, INIT_ID),
        use_case(deal.id, PARTNER_ID),
    )

    assert init_offer.ducats_escrowed == Decimal("0")
    assert partner_offer.ducats_escrowed == Decimal("0")
    assert len(client.credits) == 2
    assert {credit[0] for credit in client.credits} == {INIT_ID, PARTNER_ID}
    assert {credit[1] for credit in client.credits} == {Decimal("400")}
    assert deal.status == DealStatus.ACTIVE
    assert deal.cancelled_by_character_id in (INIT_ID, PARTNER_ID)
    assert init_offer.confirmed_revision is None
    assert partner_offer.confirmed_revision is None
